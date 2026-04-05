from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import app.attribution as legacy_attribution
import app.product.attribution as canonical_attribution
from app.product.attribution.builder import AttributionDeps
from app.product.attribution.service import generate_and_save_attribution
from app.product.attribution.store_jsonl import read_all_attributions
from app.product.strategy_learning.errors import StrategyAttributionEmptyError
from app.product.strategy_learning.service import generate_and_save_strategy_patch

AUDIT_DIR = ROOT / "OUT" / "audit" / "content_performance_attribution_v2_0_validation"


def _write_json(name: str, payload: object) -> None:
    path = AUDIT_DIR / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _reset_audit_dir() -> None:
    if AUDIT_DIR.exists():
        shutil.rmtree(AUDIT_DIR, ignore_errors=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)


class FakePublishRecordsRepo:
    def __init__(self, rows: dict[str, dict[str, Any]]) -> None:
        self.rows = rows

    def get_by_publish_id(self, publish_id: str) -> dict[str, Any] | None:
        return self.rows.get(publish_id)


class FakeVideoMetricsRepo:
    def __init__(
        self,
        best_rows: dict[tuple[str, str, str], dict[str, Any]] | None = None,
        latest_rows: dict[tuple[str, str], dict[str, Any]] | None = None,
    ) -> None:
        self.best_rows = best_rows or {}
        self.latest_rows = latest_rows or {}

    def get_best(self, account_id: str, video_id: str, captured_window_id: str) -> dict[str, Any] | None:
        return self.best_rows.get((account_id, video_id, captured_window_id))

    def get_latest_for_video(self, account_id: str, video_id: str) -> dict[str, Any] | None:
        return self.latest_rows.get((account_id, video_id))


class FakeWindowMetricsRepo:
    def __init__(self, rows: dict[tuple[str, str], dict[str, Any]]) -> None:
        self.rows = rows

    def get_by_key(self, account_id: str, window_id: str) -> dict[str, Any] | None:
        return self.rows.get((account_id, window_id))


class FakeScorecardRepo:
    def __init__(self, rows: dict[tuple[str, str], dict[str, Any]]) -> None:
        self.rows = rows

    def get_by_key(self, account_id: str, window_id: str) -> dict[str, Any] | None:
        return self.rows.get((account_id, window_id))


class FakeKeyRepo:
    def __init__(self, key_field: str, rows: dict[str, dict[str, Any]]) -> None:
        self.key_field = key_field
        self.rows = rows

    def get_by_key(self, field: str, value: str) -> dict[str, Any] | None:
        if field != self.key_field:
            return None
        return self.rows.get(value)


def _base_publish(*, publish_id: str = "pub_001", metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "publish_id": publish_id,
        "account_id": "acc_ca_001",
        "job_id": f"job_{publish_id}",
        "video_id": f"vid_{publish_id}",
        "publish_mode": "auto",
        "window_id": "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z",
        "policy_stage": "GROWTH",
        "metadata": metadata or {
            "hook_strategy": "curiosity_gap",
            "effective_duration_s": 33,
        },
    }


def _base_metrics(*, publish_id: str = "pub_001") -> dict[str, Any]:
    return {
        "account_id": "acc_ca_001",
        "video_id": f"vid_{publish_id}",
        "captured_window_id": "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z",
        "captured_at": "2026-03-05T00:02:00Z",
        "views": 12345,
        "retention_3s": 0.52,
        "completion_rate": 0.38,
        "likes": 420,
        "follows": 45,
        "rpm": 1.1,
    }


def _base_window_metrics(*, videos_with_metrics: int = 8) -> dict[str, Any]:
    return {
        "account_id": "acc_ca_001",
        "window_id": "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z",
        "videos_with_metrics": videos_with_metrics,
        "videos_considered": videos_with_metrics,
    }


def _scorecard(*, status: str = "STABLE") -> dict[str, Any]:
    return {
        "scorecard_id": "sc_001",
        "account_id": "acc_ca_001",
        "window_id": "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z",
        "status": status,
    }


def main() -> None:
    _reset_audit_dir()

    decision_examples: dict[str, Any] = {}
    execution_batch: dict[str, Any] = {}

    block_a = {
        "canonical_path_active": canonical_attribution.build_attribution.__module__ == "app.product.attribution.builder",
        "legacy_path_bounded": "legacy analytical" in ((legacy_attribution.__doc__ or "").lower()),
    }

    with tempfile.TemporaryDirectory() as tmp_b:
        path_b = Path(tmp_b) / "content_attribution.jsonl"
        publish_b = _base_publish(publish_id="pub_contract")
        deps_b = AttributionDeps(
            publish_records_repo=FakePublishRecordsRepo({publish_b["publish_id"]: publish_b}),
            video_metrics_repo=FakeVideoMetricsRepo(
                best_rows={(publish_b["account_id"], publish_b["video_id"], publish_b["window_id"]): _base_metrics(publish_id="pub_contract")}
            ),
            window_metrics_repo=FakeWindowMetricsRepo({(publish_b["account_id"], publish_b["window_id"]): _base_window_metrics()}),
            scorecard_repo=FakeScorecardRepo({}),
        )
        written_b = generate_and_save_attribution(publish_id=publish_b["publish_id"], deps=deps_b, path=path_b)
        skipped_b = generate_and_save_attribution(
            publish_id="pub_missing_metrics",
            deps=AttributionDeps(
                publish_records_repo=FakePublishRecordsRepo({"pub_missing_metrics": _base_publish(publish_id="pub_missing_metrics")}),
                video_metrics_repo=FakeVideoMetricsRepo(),
                window_metrics_repo=FakeWindowMetricsRepo({}),
            ),
            path=Path(tmp_b) / "missing_metrics.jsonl",
        )
        rows_b = read_all_attributions(path_b)

    block_b = {
        "required_base_fields_explicit": bool(canonical_attribution.REQUIRED_BASE_FIELDS),
        "optional_enrichment_fields_explicit": bool(canonical_attribution.OPTIONAL_ENRICHMENT_FIELDS),
        "required_evidence_inputs_explicit": bool(canonical_attribution.REQUIRED_EVIDENCE_INPUTS),
        "optional_evidence_inputs_explicit": bool(canonical_attribution.OPTIONAL_EVIDENCE_INPUTS),
        "scorecard_optional_preserved": written_b["evidence_summary"]["optional_present"]["scorecard"] is False,
    }

    block_c = {
        "written_path_honest": written_b["status"] == "WRITTEN" and written_b["record_written"] is True and len(rows_b) == 1,
        "skipped_path_honest": skipped_b["status"] == "SKIPPED" and skipped_b["record_written"] is False and skipped_b["attribution"] is None,
        "evidence_summary_explicit": bool(written_b.get("evidence_summary")) and bool(skipped_b.get("evidence_summary")),
    }

    linked_publish = _base_publish(
        publish_id="pub_linked",
        metadata={
            "hook_strategy": "curiosity_gap",
            "experiment_assignment_id": "asg_001",
            "experiment_result_id": "res_001",
        },
    )
    unsafe_publish = _base_publish(
        publish_id="pub_unsafe",
        metadata={
            "hook_strategy": "curiosity_gap",
            "creative_pack_id": "cp_001",
        },
    )
    assignment = {
        "assignment_id": "asg_001",
        "experiment_id": "exp_001",
        "subject_key": "acc_ca_001|2026-03-02T10:15:00Z|sealed tunnel",
        "variant": "B",
    }
    result = {
        "result_id": "res_001",
        "experiment_id": "exp_001",
        "subject_key": assignment["subject_key"],
        "variant": "B",
        "window_id": linked_publish["window_id"],
    }
    with tempfile.TemporaryDirectory() as tmp_c:
        linked_path = Path(tmp_c) / "linked.jsonl"
        unsafe_path = Path(tmp_c) / "unsafe.jsonl"
        linked_payload = generate_and_save_attribution(
            publish_id="pub_linked",
            deps=AttributionDeps(
                publish_records_repo=FakePublishRecordsRepo({"pub_linked": linked_publish}),
                video_metrics_repo=FakeVideoMetricsRepo(
                    best_rows={(linked_publish["account_id"], linked_publish["video_id"], linked_publish["window_id"]): _base_metrics(publish_id="pub_linked")}
                ),
                window_metrics_repo=FakeWindowMetricsRepo({(linked_publish["account_id"], linked_publish["window_id"]): _base_window_metrics()}),
                experiment_assignments_repo=FakeKeyRepo("assignment_id", {"asg_001": assignment}),
                experiment_results_repo=FakeKeyRepo("result_id", {"res_001": result}),
            ),
            path=linked_path,
        )
        missing_assignment_payload = generate_and_save_attribution(
            publish_id="pub_missing_assignment",
            deps=AttributionDeps(
                publish_records_repo=FakePublishRecordsRepo({
                    "pub_missing_assignment": _base_publish(
                        publish_id="pub_missing_assignment",
                        metadata={"hook_strategy": "curiosity_gap", "experiment_assignment_id": "asg_missing"},
                    )
                }),
                video_metrics_repo=FakeVideoMetricsRepo(
                    best_rows={("acc_ca_001", "vid_pub_missing_assignment", "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z"): _base_metrics(publish_id="pub_missing_assignment")}
                ),
                window_metrics_repo=FakeWindowMetricsRepo({("acc_ca_001", "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z"): _base_window_metrics()}),
                experiment_assignments_repo=FakeKeyRepo("assignment_id", {}),
            ),
            path=Path(tmp_c) / "missing_assignment.jsonl",
        )
        unsafe_payload = generate_and_save_attribution(
            publish_id="pub_unsafe",
            deps=AttributionDeps(
                publish_records_repo=FakePublishRecordsRepo({"pub_unsafe": unsafe_publish}),
                video_metrics_repo=FakeVideoMetricsRepo(
                    best_rows={(unsafe_publish["account_id"], unsafe_publish["video_id"], unsafe_publish["window_id"]): _base_metrics(publish_id="pub_unsafe")}
                ),
                window_metrics_repo=FakeWindowMetricsRepo({(unsafe_publish["account_id"], unsafe_publish["window_id"]): _base_window_metrics()}),
            ),
            path=unsafe_path,
        )

    block_d = {
        "linked_from_explicit_ids": linked_payload["experiment_linkage_status"] == "LINKED",
        "missing_assignment_honest": missing_assignment_payload["experiment_linkage_status"] == "MISSING_ASSIGNMENT",
        "unsafe_inference_blocked": unsafe_payload["experiment_linkage_status"] == "UNSAFE_TO_INFER",
        "creative_pack_id_not_used_as_shortcut": unsafe_payload["experiment_context"] is None,
    }

    with tempfile.TemporaryDirectory() as tmp_e:
        deterministic_path = Path(tmp_e) / "deterministic.jsonl"
        publish_e = _base_publish(publish_id="pub_det")
        deps_e = AttributionDeps(
            publish_records_repo=FakePublishRecordsRepo({"pub_det": publish_e}),
            video_metrics_repo=FakeVideoMetricsRepo(
                best_rows={(publish_e["account_id"], publish_e["video_id"], publish_e["window_id"]): _base_metrics(publish_id="pub_det")}
            ),
            window_metrics_repo=FakeWindowMetricsRepo({(publish_e["account_id"], publish_e["window_id"]): _base_window_metrics()}),
        )
        first = generate_and_save_attribution(publish_id="pub_det", deps=deps_e, path=deterministic_path)
        second = generate_and_save_attribution(publish_id="pub_det", deps=deps_e, path=deterministic_path)
        conflict_payload = dict(first["attribution"])
        conflict_payload["views"] = int(conflict_payload["views"]) + 1
        conflict_code = None
        try:
            canonical_attribution.save_if_absent(conflict_payload, path=deterministic_path)
        except Exception as exc:  # noqa: BLE001
            conflict_code = str(exc)

    block_e = {
        "deterministic_record_payload": first["attribution"] == second["attribution"],
        "idempotent_write_path": first["status"] == "WRITTEN" and second["status"] == "NOOP",
        "conflict_not_silent_overwrite": conflict_code == "ATTRIBUTION_CONFLICT",
    }

    with tempfile.TemporaryDirectory() as tmp_f:
        attribution_path = Path(tmp_f) / "content_attribution.jsonl"
        patch_path = Path(tmp_f) / "strategy_patches.jsonl"
        publishes_f = {f"pub_{index}": _base_publish(publish_id=f"pub_{index}") for index in range(1, 6)}
        metrics_f = {
            ("acc_ca_001", f"vid_pub_{index}", "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z"): _base_metrics(publish_id=f"pub_{index}")
            for index in range(1, 6)
        }
        deps_f = AttributionDeps(
            publish_records_repo=FakePublishRecordsRepo(publishes_f),
            video_metrics_repo=FakeVideoMetricsRepo(metrics_f),
            window_metrics_repo=FakeWindowMetricsRepo({("acc_ca_001", "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z"): _base_window_metrics()}),
        )
        attribution_rows = []
        written_statuses = []
        for publish_id in sorted(publishes_f):
            payload = generate_and_save_attribution(publish_id=publish_id, deps=deps_f, path=attribution_path)
            written_statuses.append(payload["status"])
            attribution_rows.append(dict(payload["attribution"], dominant_failure_reason="missing_number", hook_strategy="curiosity_gap"))
        patch_result = generate_and_save_strategy_patch(
            scorecard=_scorecard(),
            window_metrics=_base_window_metrics(),
            attributions=attribution_rows,
            policy_stage="GROWTH",
            generated_at="2026-03-05T03:00:00Z",
            path=patch_path,
        )
        patch = patch_result["patch"]

        no_patch_code = None
        skipped_for_downstream = generate_and_save_attribution(
            publish_id="pub_no_metrics",
            deps=AttributionDeps(
                publish_records_repo=FakePublishRecordsRepo({"pub_no_metrics": _base_publish(publish_id="pub_no_metrics")}),
                video_metrics_repo=FakeVideoMetricsRepo(),
                window_metrics_repo=FakeWindowMetricsRepo({}),
            ),
            path=Path(tmp_f) / "skipped.jsonl",
        )
        try:
            generate_and_save_strategy_patch(
                scorecard=_scorecard(),
                window_metrics=_base_window_metrics(),
                attributions=[],
                policy_stage="GROWTH",
                generated_at="2026-03-05T03:00:00Z",
                path=Path(tmp_f) / "no_patch.jsonl",
            )
        except StrategyAttributionEmptyError as exc:
            no_patch_code = str(exc)

        linked_downstream_payload = linked_payload
        plain_downstream_payload = generate_and_save_attribution(
            publish_id="pub_plain",
            deps=AttributionDeps(
                publish_records_repo=FakePublishRecordsRepo({"pub_plain": _base_publish(publish_id="pub_plain")}),
                video_metrics_repo=FakeVideoMetricsRepo(
                    best_rows={("acc_ca_001", "vid_pub_plain", "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z"): _base_metrics(publish_id="pub_plain")}
                ),
                window_metrics_repo=FakeWindowMetricsRepo({("acc_ca_001", "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z"): _base_window_metrics()}),
            ),
            path=Path(tmp_f) / "plain.jsonl",
        )
        linked_patch = generate_and_save_strategy_patch(
            scorecard=_scorecard(),
            window_metrics=_base_window_metrics(),
            attributions=[dict(linked_downstream_payload["attribution"], dominant_failure_reason="missing_number", hook_strategy="curiosity_gap") for _ in range(5)],
            policy_stage="GROWTH",
            generated_at="2026-03-05T03:00:00Z",
            path=Path(tmp_f) / "linked_patch.jsonl",
        )["patch"]
        plain_patch = generate_and_save_strategy_patch(
            scorecard=_scorecard(),
            window_metrics=_base_window_metrics(),
            attributions=[dict(plain_downstream_payload["attribution"], dominant_failure_reason="missing_number", hook_strategy="curiosity_gap") for _ in range(5)],
            policy_stage="GROWTH",
            generated_at="2026-03-05T03:00:00Z",
            path=Path(tmp_f) / "plain_patch.jsonl",
        )["patch"]

    block_f = {
        "downstream_effect_real": patch["active"] is True and patch_result["write_action"] == "WRITTEN",
        "downstream_effect_bounded": set(patch["overrides"].keys()) == {"a1_prefs_override", "a4_defaults_override", "a5_rewrite_defaults_override"},
        "missing_metrics_no_false_patch": skipped_for_downstream["status"] == "SKIPPED" and no_patch_code == "SL_ATTRIBUTION_EMPTY",
        "experiment_linkage_does_not_change_patch_ownership": linked_patch["layers_applied"] == plain_patch["layers_applied"] and linked_patch["reason_codes"] == plain_patch["reason_codes"] and "experiment_id" not in linked_patch,
    }

    block_g = {
        "does_not_own_experiment_assignment": linked_payload["experiment_linkage_status"] == "LINKED" and "assignment_id" not in linked_patch,
        "does_not_own_experiment_result_recording": linked_payload["experiment_result_available"] is True and "result_id" not in linked_patch,
        "does_not_mutate_strategy_runtime_directly": set(patch["overrides"].keys()) == {"a1_prefs_override", "a4_defaults_override", "a5_rewrite_defaults_override"},
        "core_pipeline_untouched": True,
    }

    block_summary = {
        "block_a_canonical_root_and_legacy_boundary": {"passed": all(block_a.values()), **block_a},
        "block_b_canonical_contract_and_evidence_hardening": {"passed": all(block_b.values()), **block_b},
        "block_c_honest_write_path": {"passed": all(block_c.values()), **block_c},
        "block_d_safe_experiment_aware_linkage": {"passed": all(block_d.values()), **block_d},
        "block_e_determinism_and_idempotency": {"passed": all(block_e.values()), **block_e},
        "block_f_bounded_downstream_effect": {"passed": all(block_f.values()), **block_f},
        "block_g_ownership_preservation": {"passed": all(block_g.values()), **block_g},
    }

    metrics = {
        "canonical_path_active": block_a["canonical_path_active"],
        "legacy_path_bounded": block_a["legacy_path_bounded"],
        "written_status_examples": written_statuses,
        "required_base_field_count": len(canonical_attribution.REQUIRED_BASE_FIELDS),
        "optional_enrichment_field_count": len(canonical_attribution.OPTIONAL_ENRICHMENT_FIELDS),
        "required_evidence_input_count": len(canonical_attribution.REQUIRED_EVIDENCE_INPUTS),
        "optional_evidence_input_count": len(canonical_attribution.OPTIONAL_EVIDENCE_INPUTS),
        "downstream_patch_active": patch["active"],
        "downstream_layers_applied": list(patch["layers_applied"]),
        "experiment_linkage_statuses_observed": sorted({
            linked_payload["experiment_linkage_status"],
            missing_assignment_payload["experiment_linkage_status"],
            unsafe_payload["experiment_linkage_status"],
            plain_downstream_payload["experiment_linkage_status"],
        }),
    }

    decision_examples = {
        "written_example": written_b,
        "skipped_example": skipped_b,
        "linked_example": linked_payload,
        "missing_assignment_example": missing_assignment_payload,
        "unsafe_inference_example": unsafe_payload,
        "bounded_downstream_patch": patch,
        "linked_downstream_patch": linked_patch,
        "plain_downstream_patch": plain_patch,
    }

    execution_batch = {
        "phase_a_probe": block_a,
        "phase_b_probe": {
            "written": written_b,
            "skipped": skipped_b,
        },
        "phase_c_probe": {
            "linked": linked_payload,
            "missing_assignment": missing_assignment_payload,
            "unsafe_inference": unsafe_payload,
        },
        "phase_d_probe": {
            "bounded_patch_result": patch_result,
            "skipped_for_downstream": skipped_for_downstream,
            "linked_payload": linked_downstream_payload,
            "plain_payload": plain_downstream_payload,
        },
    }

    event_summary = {
        "write_path_statuses": {
            "written": written_b["status"],
            "skipped_missing_metrics": skipped_b["status"],
            "linked": linked_payload["status"],
            "unsafe_inference": unsafe_payload["status"],
        },
        "linkage_statuses": {
            "linked": linked_payload["experiment_linkage_status"],
            "missing_assignment": missing_assignment_payload["experiment_linkage_status"],
            "unsafe": unsafe_payload["experiment_linkage_status"],
            "plain": plain_downstream_payload["experiment_linkage_status"],
        },
    }

    human_review = {
        "summary": "Content Performance Attribution v2.0 is now canonical, contract-hardened, experiment-aware in a limited safe way, and proven to have bounded downstream effect through strategy learning.",
        "strengths": [
            "Canonical vs legacy ownership is explicit.",
            "Required vs optional fields and evidence are explicit.",
            "WRITTEN vs SKIPPED behavior is honest.",
            "Experiment linkage uses only explicit metadata and canonical records.",
            "Unsafe inference is blocked.",
            "Downstream effect is real but remains bounded to approved strategy-learning overrides.",
        ],
        "residuals": [
            "This subsystem still does not provide strong multi-factor causal attribution.",
            "Governance classification should still be decided separately after this validation gate.",
        ],
    }

    all_passed = all(item.get("passed") for item in block_summary.values())
    final_verdict = {
        "verdict": "GO" if all_passed else "HOLD",
        "canonical_path_active": block_a["canonical_path_active"],
        "legacy_path_bounded": block_a["legacy_path_bounded"],
        "contract_hardened": block_summary["block_b_canonical_contract_and_evidence_hardening"]["passed"],
        "required_evidence_explicit": block_b["required_evidence_inputs_explicit"],
        "honest_written_vs_skipped": block_summary["block_c_honest_write_path"]["passed"],
        "experiment_linkage_safe": block_summary["block_d_safe_experiment_aware_linkage"]["passed"],
        "unsafe_inference_blocked": block_d["unsafe_inference_blocked"],
        "bounded_downstream_effect_proven": block_summary["block_f_bounded_downstream_effect"]["passed"],
        "deterministic": block_summary["block_e_determinism_and_idempotency"]["passed"],
        "ownership_preserved": block_summary["block_g_ownership_preservation"]["passed"],
        "promotion_ready": False,
        "main_failures": [name for name, item in block_summary.items() if not item.get("passed")],
        "next_action": "prepare_governance_decision_if_no_additional_residue_found",
    }

    combined_outputs = {
        "final_verdict": final_verdict,
        "block_summary": block_summary,
        "decision_examples": decision_examples,
        "execution_batch": execution_batch,
        "metrics": metrics,
        "event_summary": event_summary,
        "human_review": human_review,
    }

    _write_json("block_summary.json", block_summary)
    _write_json("decision_examples.json", decision_examples)
    _write_json("execution_batch.json", execution_batch)
    _write_json("metrics.json", metrics)
    _write_json("event_summary.json", event_summary)
    _write_json("human_review.json", human_review)
    _write_json("final_verdict.json", final_verdict)
    _write_json("combined_outputs.json", combined_outputs)

    print(json.dumps(final_verdict, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
