from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.creative.agents.learning.models import LearningAgentInput, LearningAgentResult
from app.creative.contracts.agent_common import FallbackDecision, FallbackMode
from app.creative.contracts.creative_pack import (
    LearningInsights,
    LearningPolicy,
    LearningPolicySignal,
    PatternFindingSummary,
)


@dataclass
class LearningAgentService:
    default_publish_records_path: Path = Path("OUT/data/publish_records/publish_records.jsonl")
    default_video_metrics_path: Path = Path("OUT/metrics/video_metrics.jsonl")
    default_analysis_dir: Path = Path("OUT/analysis")
    default_qc_events_path: Path = Path("OUT/events/events.jsonl")
    default_execution_history_dir: Path = Path("OUT")
    default_output_path: Path | None = None

    def generate(self, data: LearningAgentInput) -> LearningAgentResult:
        try:
            result = self._generate(data)
        except Exception:  # noqa: BLE001
            result = self._fallback_result()
        self._persist(result, data.output_path or self.default_output_path)
        return result

    def _generate(self, data: LearningAgentInput) -> LearningAgentResult:
        publish_rows = self._read_jsonl(data.publish_records_path or self.default_publish_records_path)
        metric_rows = self._read_jsonl(data.video_metrics_path or self.default_video_metrics_path)
        qc_event_rows = self._read_jsonl(data.qc_events_path or self.default_qc_events_path)
        analysis_dir = data.analysis_dir or self.default_analysis_dir
        hook_summary = self._read_json(analysis_dir / "hook_performance_summary.json")
        execution_rows = self._read_execution_history(data.execution_history_dir or self.default_execution_history_dir, data.account_id)

        account_publish_rows = [row for row in publish_rows if str(row.get("account_id") or "") == data.account_id]
        account_metric_rows = [row for row in metric_rows if str(row.get("account_id") or "") == data.account_id]
        account_qc_rows = [row for row in qc_event_rows if str(row.get("account_id") or "") == data.account_id]

        if (
            not account_publish_rows
            and not account_metric_rows
            and not hook_summary
            and not execution_rows
            and not account_qc_rows
        ):
            return self._fallback_result()

        recent_metrics = account_metric_rows[-20:]
        long_metrics = account_metric_rows[-100:]
        recommended_hook = self._resolve_hook_type(hook_summary)
        average_duration = self._average_numeric(recent_metrics, ("duration_s", "render_duration_s", "video_duration_s"))
        average_completion = self._average_numeric(recent_metrics, ("completion_rate", "completion", "retention_rate"))
        average_views = self._average_numeric(recent_metrics, ("views", "view_count"))

        qc_summary = self._summarize_qc(execution_rows=execution_rows, qc_event_rows=account_qc_rows)
        target_duration_range = self._resolve_duration_policy(average_duration, execution_rows)
        preferred_visual_style = "dark_backgrounds" if average_completion >= 0.4 else "phase1_baseline"
        preferred_voice_style = "calm_dark" if average_views >= 150 else "phase1_baseline"
        saturation_signal = "elevated" if len(account_publish_rows) >= 5 else "baseline"
        recommendations = [
            f"prefer_hook_type:{recommended_hook}",
            f"target_duration_range:{target_duration_range}",
        ]
        if preferred_visual_style != "phase1_baseline":
            recommendations.append(f"prefer_visual_style:{preferred_visual_style}")
        if saturation_signal != "baseline":
            recommendations.append("reduce_format_repetition")
        if qc_summary["recent_hold_or_reject_rate"] >= 0.4:
            recommendations.append("bias_conservative_quality")
        if qc_summary["avg_payoff_quality"] >= 0.75 and qc_summary["clean_execution_count"] >= 3:
            recommendations.append("bias_high_payoff_specificity")

        insights = LearningInsights(
            recommended_hook_type=recommended_hook,
            target_duration_range=target_duration_range,
            preferred_visual_style=preferred_visual_style,
            preferred_voice_style=preferred_voice_style,
            saturation_signal=saturation_signal,
            recommendations=recommendations,
            signal_summary={
                "publish_count": len(account_publish_rows),
                "metrics_count": len(account_metric_rows),
                "avg_views": average_views,
                "avg_completion_rate": average_completion,
                "avg_duration_s": average_duration,
                "recent_metrics_count": len(recent_metrics),
                "long_metrics_count": len(long_metrics),
                "qc_evidence_count": qc_summary["execution_count"],
                "clean_execution_count": qc_summary["clean_execution_count"],
                "approve_count": qc_summary["approve_count"],
                "hold_count": qc_summary["hold_count"],
                "reject_count": qc_summary["reject_count"],
                "avg_overall_score": qc_summary["avg_overall_score"],
                "avg_payoff_quality": qc_summary["avg_payoff_quality"],
                "fallback_contamination_rate": qc_summary["fallback_contamination_rate"],
            },
        )
        pattern_findings = self._build_pattern_findings(execution_rows)
        policy = self._build_learning_policy(
            recommended_hook=recommended_hook,
            target_duration_range=target_duration_range,
            qc_summary=qc_summary,
            pattern_findings=pattern_findings,
        )
        return LearningAgentResult(
            learning_insights=insights,
            learning_policy=policy,
            pattern_findings_summary=tuple(pattern_findings),
            fallback=FallbackDecision(used=False, mode=FallbackMode.NONE.value, reason=""),
        )

    def _fallback_result(self) -> LearningAgentResult:
        return LearningAgentResult(
            learning_insights=LearningInsights(
                recommended_hook_type="question",
                target_duration_range="8-12s",
                preferred_visual_style="phase1_baseline",
                preferred_voice_style="phase1_baseline",
                saturation_signal="baseline",
                recommendations=["fallback_default"],
                signal_summary={"publish_count": 0, "metrics_count": 0},
            ),
            learning_policy=LearningPolicy(
                hook_type_bias=LearningPolicySignal(value="question", confidence=0.0, evidence_count=0),
                duration_bias=LearningPolicySignal(value="8-12s", confidence=0.0, evidence_count=0),
                payoff_specificity_bias=LearningPolicySignal(value="medium", confidence=0.0, evidence_count=0),
                risk_adjustment_hint=LearningPolicySignal(value="standard", confidence=0.0, evidence_count=0),
                variation_tolerance_hint=LearningPolicySignal(value="low", confidence=0.0, evidence_count=0),
                confidence_summary={"fallback_used": True},
                policy_trace={"fallback_reason": "LEARNING_INSIGHTS_FALLBACK"},
            ),
            pattern_findings_summary=tuple(),
            fallback=FallbackDecision(
                used=True,
                mode=FallbackMode.SAFE_DEFAULT.value,
                reason="LEARNING_INSIGHTS_FALLBACK",
            ),
        )

    def _read_jsonl(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            text = line.strip()
            if not text:
                continue
            try:
                payload = json.loads(text)
            except Exception:  # noqa: BLE001
                continue
            if isinstance(payload, dict):
                rows.append(payload)
        return rows

    def _read_json(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def _read_execution_history(self, root: Path, account_id: str) -> list[dict[str, Any]]:
        if not root.exists():
            return []
        rows: list[dict[str, Any]] = []
        for path in sorted(root.rglob("execution_outputs.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                continue
            creative_pack = payload.get("creative_pack") if isinstance(payload, dict) else None
            if not isinstance(creative_pack, dict):
                continue
            if str(creative_pack.get("account_id") or "") != account_id:
                continue
            rows.append(self._extract_execution_row(payload, path))
        return rows[-100:]

    def _extract_execution_row(self, payload: dict[str, Any], path: Path) -> dict[str, Any]:
        creative_pack = payload.get("creative_pack") if isinstance(payload.get("creative_pack"), dict) else {}
        video_qc = payload.get("video_qc") if isinstance(payload.get("video_qc"), dict) else {}
        decision = video_qc.get("decision") if isinstance(video_qc.get("decision"), dict) else {}
        score_summary = decision.get("score_summary") if isinstance(decision.get("score_summary"), dict) else {}
        product_signals = decision.get("product_signals") if isinstance(decision.get("product_signals"), dict) else {}
        strategy_profile = creative_pack.get("strategy_profile") if isinstance(creative_pack.get("strategy_profile"), dict) else {}
        script_plan = creative_pack.get("script_plan") if isinstance(creative_pack.get("script_plan"), dict) else {}
        asset_plan = creative_pack.get("asset_plan") if isinstance(creative_pack.get("asset_plan"), dict) else {}
        voice_plan = creative_pack.get("voice_plan") if isinstance(creative_pack.get("voice_plan"), dict) else {}
        edit_plan = creative_pack.get("edit_plan") if isinstance(creative_pack.get("edit_plan"), dict) else {}
        learning = payload.get("learning") if isinstance(payload.get("learning"), dict) else {}
        learning_fallback = bool(((learning.get("fallback") or {}) if isinstance(learning.get("fallback"), dict) else {}).get("used"))
        asset_selection = payload.get("asset_selection") if isinstance(payload.get("asset_selection"), dict) else {}
        asset_fallback = bool(((asset_selection.get("fallback") or {}) if isinstance(asset_selection.get("fallback"), dict) else {}).get("used"))
        voice_fallback = bool(voice_plan.get("fallback_used"))
        script_generation_mode = str(script_plan.get("generation_mode") or "")
        script_fallback = script_generation_mode.startswith("fallback")
        contaminated = any((learning_fallback, asset_fallback, voice_fallback, script_fallback))

        payoff = str(script_plan.get("payoff") or "")
        visual_payoff_family = str(((asset_plan.get("segments") or {}).get("payoff") or {}).get("category") or "other")
        return {
            "source_path": str(path),
            "status": str(video_qc.get("status") or decision.get("status") or "UNKNOWN"),
            "reasons": list(video_qc.get("reasons") or decision.get("soft_failures") or []),
            "publishable": bool(video_qc.get("publishable", decision.get("publishable", False))),
            "overall_score": self._as_float(score_summary.get("overall_score")),
            "product_quality": self._as_float(score_summary.get("product_quality")),
            "hook_quality": self._as_float(product_signals.get("hook_quality")),
            "payoff_quality": self._as_float(product_signals.get("payoff_quality")),
            "variation_policy": str(strategy_profile.get("variation_policy") or "low"),
            "target_duration_range": str(strategy_profile.get("target_duration_range") or "8-12s"),
            "voice_style": str(voice_plan.get("style") or "unknown"),
            "editor_style_profile": str(edit_plan.get("editor_style_profile") or edit_plan.get("editor_version") or "unknown"),
            "visual_payoff_family": visual_payoff_family,
            "payoff_structure": self._payoff_structure(payoff),
            "contaminated": contaminated,
        }

    def _summarize_qc(self, *, execution_rows: list[dict[str, Any]], qc_event_rows: list[dict[str, Any]]) -> dict[str, Any]:
        clean_rows = [row for row in execution_rows if not bool(row.get("contaminated"))]
        source_rows = clean_rows or execution_rows
        status_counter = Counter(str(row.get("status") or "UNKNOWN") for row in execution_rows)
        if not status_counter:
            status_counter = Counter(
                str(((row.get("details") or {}) if isinstance(row.get("details"), dict) else {}).get("status") or "UNKNOWN")
                for row in qc_event_rows
            )
        execution_count = len(execution_rows)
        clean_count = len(clean_rows)
        return {
            "execution_count": execution_count,
            "clean_execution_count": clean_count,
            "approve_count": int(status_counter.get("APPROVE", 0)),
            "hold_count": int(status_counter.get("HOLD", 0)),
            "reject_count": int(status_counter.get("REJECT", 0)),
            "avg_overall_score": self._average_field(source_rows, "overall_score"),
            "avg_payoff_quality": self._average_field(source_rows, "payoff_quality"),
            "recent_hold_or_reject_rate": self._hold_reject_rate(source_rows[-20:] if source_rows else []),
            "fallback_contamination_rate": round(((execution_count - clean_count) / execution_count), 4) if execution_count else 0.0,
        }

    def _build_pattern_findings(self, execution_rows: list[dict[str, Any]]) -> list[PatternFindingSummary]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in execution_rows:
            grouped[f"payoff_structure:{row['payoff_structure']}"].append(row)
            grouped[f"visual_payoff_family:{row['visual_payoff_family']}"].append(row)
            grouped[f"variation_policy:{row['variation_policy']}"].append(row)
        findings: list[PatternFindingSummary] = []
        for pattern_name, rows in grouped.items():
            evidence_count = len(rows)
            if evidence_count == 0:
                continue
            findings.append(
                PatternFindingSummary(
                    pattern_name=pattern_name,
                    evidence_count=evidence_count,
                    approve_rate=self._status_rate(rows, "APPROVE"),
                    hold_rate=self._status_rate(rows, "HOLD"),
                    reject_rate=self._status_rate(rows, "REJECT"),
                    avg_overall_score=self._average_field(rows, "overall_score"),
                    avg_product_quality=self._average_field(rows, "product_quality"),
                    contaminated_evidence_rate=round(sum(1 for row in rows if row.get("contaminated")) / evidence_count, 4),
                )
            )
        findings.sort(key=lambda item: (-item.evidence_count, item.pattern_name))
        return findings[:8]

    def _build_learning_policy(
        self,
        *,
        recommended_hook: str,
        target_duration_range: str,
        qc_summary: dict[str, Any],
        pattern_findings: list[PatternFindingSummary],
    ) -> LearningPolicy:
        evidence_count = int(qc_summary.get("clean_execution_count") or qc_summary.get("execution_count") or 0)
        avg_overall = self._as_float(qc_summary.get("avg_overall_score"))
        avg_payoff = self._as_float(qc_summary.get("avg_payoff_quality"))
        hold_or_reject = self._as_float(qc_summary.get("recent_hold_or_reject_rate"))

        if avg_payoff >= 0.75:
            payoff_specificity = "high"
        elif avg_payoff >= 0.55:
            payoff_specificity = "medium"
        else:
            payoff_specificity = "low"

        if hold_or_reject >= 0.35 or avg_overall < 0.72:
            risk_hint = "conservative_if_low_score_cluster"
        else:
            risk_hint = "standard"

        medium_variation = next((item for item in pattern_findings if item.pattern_name == "variation_policy:medium"), None)
        low_variation = next((item for item in pattern_findings if item.pattern_name == "variation_policy:low"), None)
        if medium_variation and medium_variation.evidence_count >= 2 and medium_variation.approve_rate >= (low_variation.approve_rate if low_variation else 0.7):
            variation_hint = "medium"
            variation_confidence = medium_variation.approve_rate
            variation_evidence = medium_variation.evidence_count
        else:
            variation_hint = "low"
            variation_confidence = low_variation.approve_rate if low_variation is not None else 0.0
            variation_evidence = low_variation.evidence_count if low_variation is not None else 0

        return LearningPolicy(
            hook_type_bias=LearningPolicySignal(
                value=recommended_hook,
                confidence=self._confidence(evidence_count),
                evidence_count=evidence_count,
            ),
            duration_bias=LearningPolicySignal(
                value=target_duration_range,
                confidence=self._confidence(evidence_count),
                evidence_count=evidence_count,
            ),
            payoff_specificity_bias=LearningPolicySignal(
                value=payoff_specificity,
                confidence=max(self._confidence(evidence_count), avg_payoff),
                evidence_count=evidence_count,
            ),
            risk_adjustment_hint=LearningPolicySignal(
                value=risk_hint,
                confidence=max(self._confidence(evidence_count), min(1.0, hold_or_reject + 0.4)),
                evidence_count=evidence_count,
            ),
            variation_tolerance_hint=LearningPolicySignal(
                value=variation_hint,
                confidence=round(variation_confidence, 4),
                evidence_count=variation_evidence,
            ),
            confidence_summary={
                "clean_execution_count": evidence_count,
                "avg_overall_score": avg_overall,
                "avg_payoff_quality": avg_payoff,
                "fallback_contamination_rate": self._as_float(qc_summary.get("fallback_contamination_rate")),
            },
            policy_trace={
                "recent_hold_or_reject_rate": hold_or_reject,
                "variation_source": variation_hint,
                "pattern_findings_count": len(pattern_findings),
            },
        )

    def _resolve_hook_type(self, hook_summary: dict[str, Any]) -> str:
        hooks = hook_summary.get("hooks")
        if isinstance(hooks, list) and hooks:
            first = hooks[0]
            if isinstance(first, dict):
                for key in ("hook_style", "hook", "label", "pattern"):
                    value = str(first.get(key) or "").strip()
                    if value:
                        return value
        return "question"

    def _average_numeric(self, rows: list[dict[str, Any]], keys: tuple[str, ...]) -> float:
        values: list[float] = []
        for row in rows:
            for key in keys:
                value = row.get(key)
                if isinstance(value, (int, float)):
                    values.append(float(value))
                    break
        if not values:
            return 0.0
        return round(sum(values) / len(values), 4)

    def _average_field(self, rows: list[dict[str, Any]], key: str) -> float:
        values = [self._as_float(row.get(key)) for row in rows if self._as_float(row.get(key)) > 0]
        if not values:
            return 0.0
        return round(sum(values) / len(values), 4)

    def _status_rate(self, rows: list[dict[str, Any]], status: str) -> float:
        if not rows:
            return 0.0
        count = sum(1 for row in rows if str(row.get("status") or "") == status)
        return round(count / len(rows), 4)

    def _hold_reject_rate(self, rows: list[dict[str, Any]]) -> float:
        if not rows:
            return 0.0
        count = sum(1 for row in rows if str(row.get("status") or "") in {"HOLD", "REJECT"})
        return round(count / len(rows), 4)

    def _as_float(self, value: Any) -> float:
        if isinstance(value, (int, float)):
            return round(float(value), 4)
        return 0.0

    def _duration_bucket(self, average_duration: float) -> str:
        if average_duration <= 0:
            return "8-12s"
        if average_duration <= 12:
            return "8-12s"
        if average_duration <= 45:
            return "35-45s"
        return "45-60s"

    def _resolve_duration_policy(self, average_duration: float, execution_rows: list[dict[str, Any]]) -> str:
        if average_duration > 0:
            return self._duration_bucket(average_duration)
        clean_rows = [row for row in execution_rows if not bool(row.get("contaminated")) and str(row.get("status") or "") == "APPROVE"]
        if not clean_rows:
            return "8-12s"
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in clean_rows:
            grouped[str(row.get("target_duration_range") or "8-12s")].append(row)
        ranked = sorted(
            grouped.items(),
            key=lambda item: (
                -self._status_rate(item[1], "APPROVE"),
                -self._average_field(item[1], "overall_score"),
                -len(item[1]),
                item[0],
            ),
        )
        return ranked[0][0] if ranked else "8-12s"

    def _confidence(self, evidence_count: int) -> float:
        if evidence_count <= 0:
            return 0.0
        if evidence_count >= 20:
            return 0.85
        if evidence_count >= 10:
            return 0.72
        if evidence_count >= 5:
            return 0.6
        return 0.45

    def _payoff_structure(self, payoff: str) -> str:
        text = str(payoff or "").strip().upper()
        if not text:
            return "other"
        if "REMOVED FROM THE FLOORPLAN" in text or "MISSING FROM THE MAP" in text:
            return "named_location_removed"
        if "DOES NOT EXIST" in text or "NEVER ON THE MAP" in text:
            return "location_nonexistent"
        if "DEAD FOR YEARS" in text or "OFFICIALLY LISTED AS NON-EXISTENT" in text:
            return "impossible_identity_record"
        if "BEHIND THE DOOR" in text:
            return "presence_behind_barrier"
        return "other"

    def _persist(self, result: LearningAgentResult, output_path: Path | None) -> None:
        if output_path is None:
            return
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
