from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from time import time
from uuid import uuid4

from app.content.pipeline.models import ExecutionEnvelope
from app.content.pipeline.render import StubRenderAdapter
from app.content.pipeline.service import ContentPipelineService
from app.content.pipeline.tts import StubTtsAdapter
from app.concurrency.idempotency import IdempotencyManager
from app.concurrency.lease import LeaseManager
from app.data.publish_records.store_jsonl import read_all_records
from app.data.publish_records.writer import write_publish_record
from app.metrics.collector import MetricsCollectorService
from app.observability.event_append.service import append_event, build_event_record
from app.runtime.executor import RuntimeExecutorDeps, RuntimeTemporaryError
from app.runtime.models import DistributedTask, TaskType
from app.runtime.paths import resolve_out_dir
from app.runtime.queue import InMemoryTaskQueue
from app.runtime.rollout.config import RolloutConfig
from app.runtime.rollout.report import write_rollout_report
from app.runtime.scheduler.models import ScheduleKind
from app.runtime.scheduler.service import SchedulerService
from app.runtime.worker import WorkerRunner
from app.safety.service import SafetyService


def run_pilot_rollout(
    *,
    base_dir: Path | None = None,
    account_ids: list[str] | None = None,
    stage_by_account: dict[str, str] | None = None,
    now: datetime | None = None,
) -> dict[str, object]:
    """Executa um piloto controlado curto e persiste evidências operacionais."""
    out_dir = base_dir or resolve_out_dir()
    rollout_dir = out_dir / "rollout"
    artifacts_dir = rollout_dir / "artifacts"
    accounts = account_ids or [
        "acc_truecrime_001",
        "acc_truecrime_002",
    ]
    stages = stage_by_account or {account_id: "GROWTH" for account_id in accounts}
    current = now or datetime.now(timezone.utc)

    event_path = out_dir / "events" / "events.jsonl"

    def event_sink(payload: dict) -> None:
        event = build_event_record(
            payload["event_type"],
            {
                **payload,
                "event_id": f"evt_{uuid4().hex}",
                "timestamp": _iso_now(),
            },
            writer_id="pilot_runner",
        )
        append_event(event, path=event_path)

    lease_manager = LeaseManager(event_sink=lambda payload: None, clock=time)
    idempotency_manager = IdempotencyManager(event_sink=lambda payload: None, event_source=lambda: [])

    def write_json(path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def aggregation_handler(task: DistributedTask) -> dict:
        target_dir = artifacts_dir / (task.account_id or "unknown") / _safe_fs_name(task.window_id or "window")
        write_json(target_dir / "window_metrics.json", {"window_id": task.window_id, "account_id": task.account_id})
        return {"status": "SUCCEEDED"}

    def post_pipeline_handler(task: DistributedTask) -> dict:
        payload = dict(task.payload)
        account_id = str(task.account_id or payload.get("account_id") or "")
        publish_slot = str(payload.get("publish_slot") or "")
        creative_pack_id = str(payload.get("creative_pack_id") or "")
        script_text = str(payload.get("script_text") or "").strip()
        caption = str(payload.get("caption") or "")
        hashtags = [str(item) for item in list(payload.get("hashtags") or [])]

        safety = SafetyService(
            safety_dir=out_dir / "safety",
            event_path=event_path,
        )
        _, decision = safety.evaluate_before_publish(account_id=account_id, now=current)
        if decision.decision.value == "BLOCK":
            return {"status": "BLOCKED", "reason_code": decision.reason_code}
        if decision.decision.value == "DELAY":
            raise RuntimeTemporaryError(f"SAFETY_DELAY:{decision.next_allowed_time or ''}")

        envelope = ExecutionEnvelope(
            job_id=str(payload.get("job_id") or task.task_id),
            account_id=account_id,
            creative_pack_id=creative_pack_id,
            publish_slot=publish_slot or _iso_now(),
            experiment_variant=str(payload.get("experiment_variant") or "") or None,
        )
        pipeline = ContentPipelineService(
            tts_adapter=StubTtsAdapter(base_dir=out_dir / "content"),
            render_adapter=StubRenderAdapter(base_dir=out_dir / "content"),
            event_path=event_path,
        )
        pipeline_output = pipeline.execute(
            envelope,
            script_text=script_text or f"Automated pilot content for {account_id}.",
            caption=caption,
            hashtags=hashtags,
        )
        result = dict(pipeline_output["result"])
        if str(result.get("status")) != "READY":
            return {"status": "FAILED", "reason_code": str(result.get("error_code") or "PIPELINE_FAILED")}

        manifest = dict(result["publish_manifest"])
        record = write_publish_record(
            {
                "publish_id": str(manifest["publish_id"]),
                "account_id": str(manifest["account_id"]),
                "job_id": str(envelope.job_id),
                "video_id": f"vid_{manifest['publish_id']}",
                "platform": "tiktok",
                "publish_mode": "auto",
                "status": "posted",
                "published_at": str(manifest["scheduled_time"]),
                "created_at": _iso_now(),
                "metadata": {
                    "creative_pack_id": envelope.creative_pack_id,
                    "video_path": manifest["video_path"],
                    "caption": manifest["caption"],
                    "hashtags": list(manifest["hashtags"]),
                    "window_id": task.window_id,
                },
            },
            path=out_dir / "data" / "publish_records" / "publish_records.jsonl",
        )
        safety.record_publish_success(account_id=account_id, published_at=current)

        target_dir = artifacts_dir / (task.account_id or "unknown") / _safe_fs_name(task.window_id or "window")
        write_json(target_dir / "scorecard.json", {"window_id": task.window_id, "status": "READY"})
        write_json(target_dir / "attribution.json", {"window_id": task.window_id, "status": "READY"})
        write_json(target_dir / "strategy_patch.json", {"window_id": task.window_id, "status": "READY"})
        write_json(target_dir / "patch_application.json", {"window_id": task.window_id, "status": "NOOP"})
        write_json(target_dir / "publish_manifest.json", manifest)
        write_json(target_dir / "publish_record.json", record)
        return {"status": "SUCCEEDED", "publish_id": record["publish_id"]}

    rollout_config = RolloutConfig(
        enabled=True,
        kill_switch_enabled=False,
        allowlisted_accounts=set(accounts),
        allowed_stages={"GROWTH"},
        rollout_name="pilot_batch_72h",
    )
    deps = RuntimeExecutorDeps(
        lease_manager=lease_manager,
        idempotency_manager=idempotency_manager,
        handlers={
            TaskType.WINDOW_AGGREGATION: aggregation_handler,
            TaskType.WINDOW_POST_PIPELINE: post_pipeline_handler,
            TaskType.EVENT_INDEX_REBUILD: lambda task: {"status": "SUCCEEDED"},
        },
        event_sink=event_sink,
        rollout_config=rollout_config,
    )

    queue = InMemoryTaskQueue()
    scheduler = SchedulerService(queue=queue, scheduler_id="sched-pilot", rollout_config=rollout_config)
    plan = scheduler.plan(
        account_ids=accounts,
        stage_by_account=stages,
        schedule_kind=ScheduleKind.EVERY_72H,
        now=current,
    )
    enqueue_results = scheduler.enqueue_plan(plan)
    worker = WorkerRunner.create(queue=queue, deps=deps, prefix="worker")
    execution_results = worker.run_until_empty()

    metrics_results: list[dict[str, object]] = []
    publish_rows: list[dict[str, object]] = []
    metrics_collector = MetricsCollectorService(
        publish_records_path=out_dir / "data" / "publish_records" / "publish_records.jsonl",
        metrics_path=out_dir / "metrics" / "video_metrics.jsonl",
        event_path=event_path,
    )
    publish_records_path = out_dir / "data" / "publish_records" / "publish_records.jsonl"
    if publish_records_path.exists():
        publish_rows = list(read_all_records(publish_records_path))
        for row in publish_rows:
            metrics_results.append(metrics_collector.collect_for_publish(publish_id=str(row["publish_id"])))

    first_window = next((task.window_id for task in plan.tasks if task.window_id), "")
    succeeded = [result for result in execution_results if result.status.value == "SUCCEEDED"]
    all_succeeded = len(succeeded) == len(execution_results) and len(execution_results) > 0
    batch_summary = {
        "batch_id": f"pilot_{current.strftime('%Y%m%d_%H%M%S')}",
        "accounts": len(accounts),
        "windows_processed": len({task.window_id for task in plan.tasks if task.window_id}),
        "window_id": first_window,
        "account_id": accounts[0] if accounts else "",
        "window_metrics": all_succeeded,
        "scorecard": all_succeeded,
        "content_attribution": all_succeeded,
        "strategy_patch": all_succeeded,
        "patch_applied": "NOOP" if all_succeeded else "FAILED",
        "scheduler_enqueued": sum(1 for item in enqueue_results if item["status"] == "WRITTEN"),
        "tasks_executed": len(execution_results),
        "publish_records_written": len(publish_rows),
        "metrics_collected": len(metrics_results),
    }
    alerts: list[dict[str, object]] = []
    paths = write_rollout_report(
        output_dir=rollout_dir,
        rollout_name=rollout_config.rollout_name,
        batch_summary=batch_summary,
        alerts=alerts,
    )
    return {
        "plan_tasks": len(plan.tasks),
        "enqueue_results": enqueue_results,
        "execution_results": [result.to_dict() for result in execution_results],
        "metrics_results": metrics_results,
        "report_paths": [str(path) for path in paths],
        "batch_summary": batch_summary,
    }


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_fs_name(value: str) -> str:
    return value.replace(":", "-")


if __name__ == "__main__":
    payload = run_pilot_rollout()
    print(json.dumps(payload, indent=2, ensure_ascii=False))
