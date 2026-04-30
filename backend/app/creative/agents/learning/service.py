from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from app.creative.agents.learning.models import LearningAgentInput, LearningAgentResult
from app.creative.contracts.agent_common import FallbackDecision, FallbackMode
from app.creative.contracts.creative_pack import (
    LearningInsights,
    LearningPolicy,
    LearningPolicySignal,
    LearningStrategyPressure,
    LearningStrategyPressureTarget,
    PatternFindingSummary,
)
from app.learning.contamination_guard import LearningContaminationGuard
from app.learning.confidence_calibrator import ConfidenceCalibration, LearningConfidenceCalibrator
from app.learning.qc_evidence_analyzer import QCEvidenceAnalyzer
from app.learning.temporal_weighting import EvidenceItem, TemporalWeightingEngine
from app.learning.trace_builder import LearningTraceBuilder


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
        qc_analysis = dict(qc_summary.get("qc_analysis") or {})
        pattern_findings = self._build_pattern_findings(execution_rows)
        contamination_evidence_items = self._build_contamination_evidence_items(
            execution_rows=execution_rows,
            account_metric_rows=account_metric_rows,
            account_qc_rows=account_qc_rows,
        )
        contamination_summary = LearningContaminationGuard().summarize_dataset(
            contamination_evidence_items
        ).to_dict()
        temporal_analysis = TemporalWeightingEngine().apply_weighting(
            self._build_temporal_evidence_items(
                execution_rows=execution_rows,
                account_metric_rows=account_metric_rows,
            )
        ).to_dict()
        calibrator = LearningConfidenceCalibrator()
        confidence_inputs = self._build_confidence_inputs(
            qc_analysis=qc_analysis,
            pattern_findings=pattern_findings,
            account_publish_rows=account_publish_rows,
            account_metric_rows=account_metric_rows,
            execution_rows=execution_rows,
            account_qc_rows=account_qc_rows,
            hook_summary=hook_summary,
            temporal_analysis=temporal_analysis,
            contamination_summary=contamination_summary,
        )
        insight_calibration = calibrator.calibrate_insight_confidence(**confidence_inputs)
        policy_calibration = calibrator.calibrate_policy_confidence(**confidence_inputs)
        confidence_summary = calibrator.summarize_confidence([insight_calibration, policy_calibration])
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

        policy = self._build_learning_policy(
            recommended_hook=recommended_hook,
            target_duration_range=target_duration_range,
            qc_summary=qc_summary,
            pattern_findings=pattern_findings,
            confidence_calibration=policy_calibration,
            confidence_inputs=confidence_inputs,
            contamination_summary=contamination_summary,
        )
        trace_builder = LearningTraceBuilder()
        learning_trace = trace_builder.build_learning_trace(
            evidence_items=contamination_evidence_items,
            qc_analysis=qc_analysis,
            confidence_calibration=insight_calibration,
            confidence_inputs=confidence_inputs,
            confidence_summary=confidence_summary,
            temporal_analysis=temporal_analysis,
            contamination_summary=contamination_summary,
            strategy_pressure=policy.strategy_pressure,
            pattern_findings=pattern_findings,
        )
        policy_trace = trace_builder.build_policy_trace(
            evidence_items=contamination_evidence_items,
            confidence_calibration=policy_calibration,
            temporal_analysis=temporal_analysis,
            contamination_summary=contamination_summary,
            strategy_pressure=policy.strategy_pressure,
            existing_policy_trace=policy.policy_trace,
        )
        policy = replace(policy, policy_trace=policy_trace)

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
                "qc_approve_rate": qc_analysis.get("approve_rate", 0.0),
                "qc_hold_rate": qc_analysis.get("hold_rate", 0.0),
                "qc_reject_rate": qc_analysis.get("reject_rate", 0.0),
                "qc_clean_sample_size": qc_analysis.get("clean_sample_size", 0),
            },
            qc_summary={
                "approve_rate": qc_analysis.get("approve_rate", 0.0),
                "hold_rate": qc_analysis.get("hold_rate", 0.0),
                "reject_rate": qc_analysis.get("reject_rate", 0.0),
                "avg_scores": qc_analysis.get("avg_scores", {}),
                "sample_size": qc_analysis.get("sample_size", 0),
                "clean_sample_size": qc_analysis.get("clean_sample_size", 0),
                "contamination_rate": qc_analysis.get("contamination_rate", 0.0),
                "cluster_breakdown": qc_analysis.get("cluster_breakdown", {}),
            },
            qc_patterns=list(qc_analysis.get("patterns") or []),
            qc_confidence_summary=dict(qc_analysis.get("confidence_summary") or {}),
            temporal_analysis={
                "recent_weight": temporal_analysis.get("recent_weight", 0.0),
                "mid_term_weight": temporal_analysis.get("mid_term_weight", 0.0),
                "long_term_weight": temporal_analysis.get("long_term_weight", 0.0),
                "dominant_window": temporal_analysis.get("dominant_window", "recent"),
                "pattern_type": temporal_analysis.get("pattern_type", "volatile"),
                "staleness_detected": temporal_analysis.get("staleness_detected", False),
                "volatility_detected": temporal_analysis.get("volatility_detected", False),
                "weighted_sample_size": temporal_analysis.get("weighted_sample_size", 0.0),
                "weighted_signal_strength": temporal_analysis.get("weighted_signal_strength", 0.0),
                "weighted_consistency": temporal_analysis.get("weighted_consistency", 0.0),
            },
            contamination_summary={
                "sample_size": contamination_summary.get("sample_size", 0),
                "clean_sample_size": contamination_summary.get("clean_sample_size", 0),
                "contamination_rate": contamination_summary.get("contamination_rate", 0.0),
                "weak_signal_rate": contamination_summary.get("weak_signal_rate", 0.0),
                "insufficient_rate": contamination_summary.get("insufficient_rate", 0.0),
                "dominant_problem": contamination_summary.get("dominant_problem", "none"),
                "policy_safe": contamination_summary.get("policy_safe", False),
            },
            noise_summary={
                "noise_rate": contamination_summary.get("noise_rate", 0.0),
                "noisy_count": (contamination_summary.get("cluster_report") or {}).get("noisy_count", 0),
                "usable_for_patterning": (contamination_summary.get("cluster_report") or {}).get("usable_for_patterning", False),
                "dominant_label": (contamination_summary.get("cluster_report") or {}).get("dominant_label", "INSUFFICIENT"),
            },
            confidence=insight_calibration.confidence,
            confidence_components=dict(insight_calibration.confidence_components),
            confidence_rationale=dict(insight_calibration.confidence_rationale),
            learning_trace=learning_trace,
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
                qc_summary={
                    "approve_rate": 0.0,
                    "hold_rate": 0.0,
                    "reject_rate": 0.0,
                    "sample_size": 0,
                    "clean_sample_size": 0,
                    "contamination_rate": 0.0,
                },
                qc_patterns=[],
                qc_confidence_summary={"adjusted_confidence": 0.0, "sample_size": 0},
                temporal_analysis={
                    "recent_weight": 0.0,
                    "mid_term_weight": 0.0,
                    "long_term_weight": 0.0,
                    "dominant_window": "recent",
                    "pattern_type": "stale_signal",
                    "staleness_detected": True,
                    "volatility_detected": False,
                },
                contamination_summary={
                    "sample_size": 0,
                    "clean_sample_size": 0,
                    "contamination_rate": 0.0,
                    "weak_signal_rate": 0.0,
                    "insufficient_rate": 1.0,
                    "dominant_problem": "insufficient",
                    "policy_safe": False,
                },
                noise_summary={
                    "noise_rate": 0.0,
                    "noisy_count": 0,
                    "usable_for_patterning": False,
                    "dominant_label": "INSUFFICIENT",
                },
                confidence=0.0,
                confidence_components={
                    "sample_size": 0.0,
                    "cleanliness": 0.0,
                    "recency": 0.0,
                    "consistency": 0.0,
                    "signal_strength": 0.0,
                    "bootstrap_bias_penalty": 0.38,
                    "controlled_validation_penalty": 0.0,
                },
                confidence_rationale={
                    "sample_size": 0,
                    "clean_sample_size": 0,
                    "contamination_rate": 0.0,
                    "dominant_evidence_source": "none",
                    "bootstrap_bias_risk": "high",
                },
                learning_trace={
                    "lineage_summary": {
                        "total_evidence_count": 0,
                        "clean_evidence_count": 0,
                        "contaminated_evidence_count": 0,
                        "weak_signal_count": 0,
                        "insufficient_count": 0,
                        "noisy_count": 0,
                        "dominant_source_type": "none",
                        "controlled_validation_dominance": False,
                        "real_runtime_support": "none",
                        "evidence_references": [],
                    },
                    "qc_analysis": {
                        "sample_size": 0,
                        "approve_rate": 0.0,
                        "top_patterns": [],
                        "confidence_summary": {"adjusted_confidence": 0.0, "sample_size": 0},
                        "contamination_rate": 0.0,
                    },
                    "confidence_calibration": {
                        "sample_size": 0,
                        "clean_sample_size": 0,
                        "contamination_rate": 0.0,
                        "signal_consistency": 0.0,
                        "signal_strength": 0.0,
                        "bootstrap_bias_risk": "high",
                        "controlled_validation_dominance": False,
                        "temporal_pattern_type": "stale_signal",
                        "final_confidence": 0.0,
                    },
                    "temporal_analysis": {
                        "recent_weight": 0.0,
                        "mid_term_weight": 0.0,
                        "long_term_weight": 0.0,
                        "dominant_window": "recent",
                        "pattern_type": "stale_signal",
                        "staleness_detected": True,
                        "volatility_detected": False,
                    },
                    "contamination_analysis": {
                        "sample_size": 0,
                        "clean_sample_size": 0,
                        "contamination_rate": 0.0,
                        "noise_rate": 0.0,
                        "weak_signal_rate": 0.0,
                        "insufficient_rate": 1.0,
                        "dominant_problem": "insufficient",
                        "policy_safe": False,
                    },
                    "strategy_pressure": {
                        "pressure_mode": "weak_bias",
                        "pressure_targets": [],
                        "confidence": 0.0,
                        "bounded": True,
                        "strategy_influence_mode": "bounded",
                        "strategy_override_allowed": True,
                        "higher_authority_constraints_apply": True,
                        "pressure_origin_summary": {
                            "confidence": 0.0,
                            "policy_strength": "weak",
                            "temporal_pattern_type": "stale_signal",
                            "dominant_problem": "insufficient",
                            "policy_safe": False,
                            "clean_sample_size": 0,
                            "evidence_count": 0,
                            "pressure_capped": False,
                        },
                    },
                    "policy_safety_summary": {
                        "policy_safe": False,
                        "reason_codes": ["LEARNING_FALLBACK", "CLEAN_SAMPLE_TOO_SMALL"],
                        "confidence_level": "low",
                        "pressure_mode": "weak_bias",
                        "blocking_issues": ["fallback_result", "clean_sample_size_below_policy_threshold"],
                        "warnings": ["Learning fallback has no evidence lineage."],
                    },
                    "pattern_rationale": [],
                    "downgraded_evidence": [],
                },
            ),
            learning_policy=LearningPolicy(
                hook_type_bias=LearningPolicySignal(value="question", confidence=0.0, evidence_count=0),
                duration_bias=LearningPolicySignal(value="8-12s", confidence=0.0, evidence_count=0),
                payoff_specificity_bias=LearningPolicySignal(value="medium", confidence=0.0, evidence_count=0),
                risk_adjustment_hint=LearningPolicySignal(value="standard", confidence=0.0, evidence_count=0),
                variation_tolerance_hint=LearningPolicySignal(value="low", confidence=0.0, evidence_count=0),
                strategy_pressure=LearningStrategyPressure(
                    pressure_mode="weak_bias",
                    pressure_targets=[],
                    confidence=0.0,
                    pressure_origin_summary={
                        "confidence": 0.0,
                        "policy_strength": "weak",
                        "temporal_pattern_type": "stale_signal",
                        "dominant_problem": "insufficient",
                        "policy_safe": False,
                        "clean_sample_size": 0,
                        "evidence_count": 0,
                        "pressure_capped": False,
                    },
                ),
                confidence_summary={
                    "fallback_used": True,
                    "confidence": 0.0,
                    "policy_strength": "weak",
                    "contamination_impact": {
                        "dominant_problem": "insufficient",
                        "policy_safe": False,
                        "confidence_penalty": 0.0,
                    },
                    "confidence_rationale": {
                        "sample_size": 0,
                        "clean_sample_size": 0,
                        "bootstrap_bias_risk": "high",
                    },
                },
                policy_trace={
                    "fallback_reason": "LEARNING_INSIGHTS_FALLBACK",
                    "confidence_calibration": {"final_confidence": 0.0, "policy_strength": "weak"},
                    "contamination_analysis": {
                        "dominant_problem": "insufficient",
                        "policy_safe": False,
                    },
                    "strategy_pressure": {
                        "pressure_mode": "weak_bias",
                        "pressure_targets": [],
                        "confidence": 0.0,
                        "bounded": True,
                        "strategy_influence_mode": "bounded",
                        "strategy_override_allowed": True,
                        "higher_authority_constraints_apply": True,
                        "pressure_origin_summary": {
                            "confidence": 0.0,
                            "policy_strength": "weak",
                            "temporal_pattern_type": "stale_signal",
                            "dominant_problem": "insufficient",
                            "policy_safe": False,
                            "clean_sample_size": 0,
                            "evidence_count": 0,
                            "pressure_capped": False,
                        },
                    },
                    "lineage_summary": {
                        "total_evidence_count": 0,
                        "clean_evidence_count": 0,
                        "dominant_source_type": "none",
                        "real_runtime_support": "none",
                    },
                    "confidence_formation": {
                        "final_confidence": 0.0,
                        "policy_strength": "weak",
                        "bootstrap_bias_risk": "high",
                        "penalties_applied": ["fallback_result", "insufficient_clean_sample"],
                    },
                    "final_safety_classification": {
                        "policy_safe": False,
                        "reason_codes": ["LEARNING_FALLBACK", "CLEAN_SAMPLE_TOO_SMALL"],
                        "confidence_level": "low",
                        "pressure_mode": "weak_bias",
                        "blocking_issues": ["fallback_result", "clean_sample_size_below_policy_threshold"],
                        "warnings": ["Learning fallback has no evidence lineage."],
                    },
                },
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
            "timestamp": str(
                payload.get("generated_at")
                or creative_pack.get("generated_at")
                or video_qc.get("timestamp")
                or decision.get("timestamp")
                or ""
            ),
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
            "payoff_specificity": "specific" if self._payoff_structure(payoff) != "other" else "low",
            "payoff_text": payoff,
            "hook_type": str(script_plan.get("hook_type") or script_plan.get("hook_style") or "unknown"),
            "script_fallback": script_fallback,
            "voice_fallback": voice_fallback,
            "asset_fallback": asset_fallback,
            "contaminated": contaminated,
        }

    def _summarize_qc(self, *, execution_rows: list[dict[str, Any]], qc_event_rows: list[dict[str, Any]]) -> dict[str, Any]:
        qc_analysis = QCEvidenceAnalyzer().analyze(
            [
                *[self._execution_row_to_qc_result(row) for row in execution_rows],
                *[self._qc_event_row_to_qc_result(row) for row in qc_event_rows],
            ]
        ).to_dict()
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
            "qc_analysis": qc_analysis,
        }

    def _execution_row_to_qc_result(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": str(row.get("status") or "UNKNOWN"),
            "publishable": bool(row.get("publishable")),
            "overall_score": self._as_float(row.get("overall_score")),
            "hook_score": self._as_float(row.get("hook_quality")),
            "payoff_score": self._as_float(row.get("payoff_quality")),
            "product_score": self._as_float(row.get("product_quality")),
            "technical_valid": True,
            "script_metadata": {
                "hook_type": str(row.get("hook_type") or "unknown"),
                "payoff_specificity": str(row.get("payoff_specificity") or row.get("payoff_structure") or "unknown"),
                "payoff": str(row.get("payoff_text") or ""),
                "fallback_used": bool(row.get("script_fallback")),
            },
            "asset_metadata": {
                "visual_payoff_family": str(row.get("visual_payoff_family") or "unknown"),
                "fallback_used": bool(row.get("asset_fallback")),
            },
            "voice_metadata": {
                "voice_style": str(row.get("voice_style") or "unknown"),
                "fallback_used": bool(row.get("voice_fallback")),
            },
            "contaminated": bool(row.get("contaminated")),
            "timestamp": str(row.get("timestamp") or ""),
        }

    def _qc_event_row_to_qc_result(self, row: dict[str, Any]) -> dict[str, Any]:
        details = row.get("details") if isinstance(row.get("details"), dict) else row
        score_summary = details.get("score_summary") if isinstance(details.get("score_summary"), dict) else {}
        product_signals = details.get("product_signals") if isinstance(details.get("product_signals"), dict) else {}
        return {
            "status": str(details.get("status") or row.get("status") or "UNKNOWN"),
            "publishable": bool(details.get("publishable", row.get("publishable", False))),
            "overall_score": self._as_float(score_summary.get("overall_score") or details.get("overall_score")),
            "hook_score": self._as_float(product_signals.get("hook_quality") or details.get("hook_score")),
            "payoff_score": self._as_float(product_signals.get("payoff_quality") or details.get("payoff_score")),
            "product_score": self._as_float(score_summary.get("product_quality") or details.get("product_score")),
            "technical_valid": bool(details.get("technical_valid", True)),
            "script_metadata": details.get("script_metadata") if isinstance(details.get("script_metadata"), dict) else {},
            "asset_metadata": details.get("asset_metadata") if isinstance(details.get("asset_metadata"), dict) else {},
            "voice_metadata": details.get("voice_metadata") if isinstance(details.get("voice_metadata"), dict) else {},
            "fallback_used": bool(details.get("fallback_used", False)),
            "timestamp": str(details.get("timestamp") or row.get("timestamp") or ""),
        }

    def _build_temporal_evidence_items(
        self,
        *,
        execution_rows: list[dict[str, Any]],
        account_metric_rows: list[dict[str, Any]],
    ) -> list[EvidenceItem]:
        items: list[EvidenceItem] = []
        for row in execution_rows:
            raw_value = self._as_float(row.get("overall_score")) or self._as_float(row.get("product_quality"))
            if raw_value <= 0:
                continue
            items.append(
                EvidenceItem(
                    raw_value=raw_value,
                    timestamp=str(row.get("timestamp") or ""),
                    contaminated=bool(row.get("contaminated")),
                    source="runtime_history",
                    metadata={"status": str(row.get("status") or "UNKNOWN")},
                )
            )
        for row in account_metric_rows:
            raw_value = self._metric_signal_value(row)
            if raw_value <= 0:
                continue
            items.append(
                EvidenceItem(
                    raw_value=raw_value,
                    timestamp=str(
                        row.get("timestamp")
                        or row.get("captured_at")
                        or row.get("published_at")
                        or row.get("created_at")
                        or ""
                    ),
                    contaminated=bool(row.get("contaminated") or row.get("fallback_used")),
                    source="post_publish_metrics",
                    metadata={"metric_row": True},
                )
            )
        return items

    def _build_contamination_evidence_items(
        self,
        *,
        execution_rows: list[dict[str, Any]],
        account_metric_rows: list[dict[str, Any]],
        account_qc_rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for row in execution_rows:
            items.append(
                {
                    "source_type": "runtime_history",
                    "source_id": str(row.get("source_path") or ""),
                    "timestamp": str(row.get("timestamp") or ""),
                    "status": str(row.get("status") or "UNKNOWN"),
                    "overall_score": self._as_float(row.get("overall_score")),
                    "product_quality": self._as_float(row.get("product_quality")),
                    "fallback_used": bool(row.get("contaminated")),
                    "script_fallback": bool(row.get("script_fallback")),
                    "asset_fallback": bool(row.get("asset_fallback")),
                    "voice_fallback": bool(row.get("voice_fallback")),
                    "metadata": {
                        "payoff_structure": str(row.get("payoff_structure") or ""),
                        "visual_payoff_family": str(row.get("visual_payoff_family") or ""),
                        "variation_policy": str(row.get("variation_policy") or ""),
                    },
                }
            )
        for index, row in enumerate(account_metric_rows):
            items.append(
                {
                    "source_type": "post_publish_metrics",
                    "source_id": str(row.get("metric_id") or row.get("publish_id") or f"metric_row:{index}"),
                    "timestamp": str(
                        row.get("timestamp")
                        or row.get("captured_at")
                        or row.get("published_at")
                        or row.get("created_at")
                        or ""
                    ),
                    "status": "APPROVE" if self._metric_signal_value(row) >= 0.7 else "HOLD",
                    "raw_value": self._metric_signal_value(row),
                    "fallback_used": bool(row.get("fallback_used") or row.get("contaminated")),
                    "metadata": {"metric_row": True},
                }
            )
        for index, row in enumerate(account_qc_rows):
            details = row.get("details") if isinstance(row.get("details"), dict) else row
            score_summary = details.get("score_summary") if isinstance(details.get("score_summary"), dict) else {}
            items.append(
                {
                    "source_type": "qc_result",
                    "source_id": str(row.get("event_id") or row.get("id") or f"qc_event:{index}"),
                    "timestamp": str(details.get("timestamp") or row.get("timestamp") or ""),
                    "status": str(details.get("status") or row.get("status") or "UNKNOWN"),
                    "overall_score": self._as_float(score_summary.get("overall_score") or details.get("overall_score")),
                    "fallback_used": bool(details.get("fallback_used") or row.get("fallback_used")),
                    "metadata": {
                        "event_type": str(row.get("event_type") or ""),
                        "source": "qc_event",
                    },
                    "missing_metadata": not bool(details),
                }
            )
        return items

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
            contaminated_rate = round(sum(1 for row in rows if row.get("contaminated")) / evidence_count, 4)
            clean_count = sum(1 for row in rows if not row.get("contaminated"))
            approve_rate = self._status_rate(rows, "APPROVE")
            hold_rate = self._status_rate(rows, "HOLD")
            reject_rate = self._status_rate(rows, "REJECT")
            confidence = LearningConfidenceCalibrator().calibrate_insight_confidence(
                sample_size=evidence_count,
                clean_sample_size=clean_count,
                contamination_rate=contaminated_rate,
                recency_weight=self._recency_weight(rows, []),
                signal_consistency=max(approve_rate, hold_rate, reject_rate),
                signal_strength=abs(approve_rate - max(hold_rate, reject_rate)),
                evidence_source_mix={"runtime_history": evidence_count},
                evidence_variety=len({str(row.get("variation_policy") or "") for row in rows if row.get("variation_policy")}),
                cluster_distribution={"APPROVE": int(round(approve_rate * evidence_count)), "HOLD": int(round(hold_rate * evidence_count)), "REJECT": int(round(reject_rate * evidence_count))},
            )
            findings.append(
                PatternFindingSummary(
                    pattern_name=pattern_name,
                    evidence_count=evidence_count,
                    approve_rate=approve_rate,
                    hold_rate=hold_rate,
                    reject_rate=reject_rate,
                    avg_overall_score=self._average_field(rows, "overall_score"),
                    avg_product_quality=self._average_field(rows, "product_quality"),
                    contaminated_evidence_rate=contaminated_rate,
                    confidence=confidence.confidence,
                    confidence_rationale=dict(confidence.confidence_rationale),
                )
            )
        findings.sort(key=lambda item: (-item.evidence_count, item.pattern_name))
        return findings[:8]

    def _build_confidence_inputs(
        self,
        *,
        qc_analysis: dict[str, Any],
        pattern_findings: list[PatternFindingSummary],
        account_publish_rows: list[dict[str, Any]],
        account_metric_rows: list[dict[str, Any]],
        execution_rows: list[dict[str, Any]],
        account_qc_rows: list[dict[str, Any]],
        hook_summary: dict[str, Any],
        temporal_analysis: dict[str, Any],
        contamination_summary: dict[str, Any],
    ) -> dict[str, Any]:
        confidence_summary = (qc_analysis.get("confidence_summary") or {}) if isinstance(qc_analysis.get("confidence_summary"), dict) else {}
        cluster_breakdown = (qc_analysis.get("cluster_breakdown") or {}) if isinstance(qc_analysis.get("cluster_breakdown"), dict) else {}
        qc_sample_size = int(qc_analysis.get("sample_size") or 0)
        qc_clean_sample_size = int(qc_analysis.get("clean_sample_size") or 0)
        guard_clean_sample_size = int(contamination_summary.get("clean_sample_size") or qc_clean_sample_size)
        runtime_history_count = len(account_publish_rows) + len(account_metric_rows) + len(execution_rows)
        controlled_validation_count = self._controlled_validation_count(hook_summary)
        sample_size = qc_sample_size + len(account_metric_rows) + controlled_validation_count
        clean_sample_size = min(qc_clean_sample_size + len(account_metric_rows), guard_clean_sample_size + len(account_metric_rows))
        if sample_size <= 0 and runtime_history_count > 0:
            sample_size = runtime_history_count
            clean_sample_size = runtime_history_count

        temporal_sample_size = self._as_float(temporal_analysis.get("weighted_sample_size"))
        temporal_consistency = self._as_float(temporal_analysis.get("weighted_consistency"))
        temporal_signal_strength = self._as_float(temporal_analysis.get("weighted_signal_strength"))
        base_consistency = self._as_float(confidence_summary.get("consistency")) or self._pattern_consistency(pattern_findings)
        base_signal_strength = self._as_float(confidence_summary.get("signal_strength")) or self._pattern_signal_strength(pattern_findings)
        return {
            "sample_size": sample_size,
            "clean_sample_size": min(clean_sample_size, sample_size),
            "contamination_rate": self._as_float(qc_analysis.get("contamination_rate")),
            "recency_weight": self._as_float(temporal_analysis.get("weighted_recency_score")) or self._recency_weight(account_metric_rows, execution_rows),
            "signal_consistency": self._blend_signal(base_consistency, temporal_consistency, temporal_sample_size),
            "signal_strength": self._blend_signal(base_signal_strength, temporal_signal_strength, temporal_sample_size),
            "evidence_source_mix": {
                "qc_derived": qc_sample_size,
                "runtime_history": runtime_history_count,
                "controlled_validation": controlled_validation_count,
                "post_publish_metrics": len(account_metric_rows),
            },
            "evidence_variety": self._evidence_variety(pattern_findings, execution_rows),
            "cluster_distribution": self._cluster_distribution(cluster_breakdown),
            "temporal_pattern_type": str(temporal_analysis.get("pattern_type") or "unknown"),
            "contamination_summary": {
                "contamination_rate": self._as_float(contamination_summary.get("contamination_rate")),
                "weak_signal_rate": self._as_float(contamination_summary.get("weak_signal_rate")),
                "noise_rate": self._as_float(contamination_summary.get("noise_rate")),
                "insufficient_rate": self._as_float(contamination_summary.get("insufficient_rate")),
                "dominant_problem": str(contamination_summary.get("dominant_problem") or "none"),
                "policy_safe": bool(contamination_summary.get("policy_safe", False)),
                "confidence_penalty": self._as_float(contamination_summary.get("confidence_penalty")),
            },
        }

    def _controlled_validation_count(self, hook_summary: dict[str, Any]) -> int:
        hooks = hook_summary.get("hooks") if isinstance(hook_summary, dict) else None
        if isinstance(hooks, list):
            return len([item for item in hooks if isinstance(item, dict)]) or 1
        return 1 if hook_summary else 0

    def _recency_weight(self, metric_or_execution_rows: list[dict[str, Any]], execution_rows: list[dict[str, Any]]) -> float:
        total = len(metric_or_execution_rows) + len(execution_rows)
        if total <= 0:
            return 0.0
        recent_weight = min(total / 20.0, 1.0)
        return round(0.25 + (recent_weight * 0.65), 4)

    def _blend_signal(self, base_value: float, temporal_value: float, temporal_sample_size: float) -> float:
        base_value = self._as_float(base_value)
        temporal_value = self._as_float(temporal_value)
        if temporal_sample_size <= 0:
            return base_value
        if base_value <= 0:
            return temporal_value
        return round((base_value * 0.7) + (temporal_value * 0.3), 4)

    def _metric_signal_value(self, row: dict[str, Any]) -> float:
        completion = self._as_float(row.get("completion_rate") or row.get("completion") or row.get("retention_rate"))
        if completion > 0:
            return completion
        views = self._as_float(row.get("views") or row.get("view_count"))
        if views <= 0:
            return 0.0
        return round(min(1.0, views / 1000.0), 4)

    def _pattern_consistency(self, pattern_findings: list[PatternFindingSummary]) -> float:
        if not pattern_findings:
            return 0.0
        values = [max(item.approve_rate, item.hold_rate, item.reject_rate) for item in pattern_findings]
        return round(sum(values) / len(values), 4)

    def _pattern_signal_strength(self, pattern_findings: list[PatternFindingSummary]) -> float:
        if not pattern_findings:
            return 0.0
        strengths = [
            abs(item.approve_rate - max(item.hold_rate, item.reject_rate))
            for item in pattern_findings
        ]
        return round(sum(strengths) / len(strengths), 4)

    def _evidence_variety(self, pattern_findings: list[PatternFindingSummary], execution_rows: list[dict[str, Any]]) -> int:
        values = {item.pattern_name for item in pattern_findings}
        values.update(str(row.get("variation_policy") or "") for row in execution_rows if row.get("variation_policy"))
        values.update(str(row.get("visual_payoff_family") or "") for row in execution_rows if row.get("visual_payoff_family"))
        values.discard("")
        return len(values)

    def _cluster_distribution(self, cluster_breakdown: dict[str, Any]) -> dict[str, int]:
        distribution: dict[str, int] = {}
        for key, value in cluster_breakdown.items():
            if isinstance(value, dict):
                distribution[str(key).upper()] = int(value.get("count") or 0)
        return distribution

    def _build_learning_policy(
        self,
        *,
        recommended_hook: str,
        target_duration_range: str,
        qc_summary: dict[str, Any],
        pattern_findings: list[PatternFindingSummary],
        confidence_calibration: ConfidenceCalibration,
        confidence_inputs: dict[str, Any],
        contamination_summary: dict[str, Any],
    ) -> LearningPolicy:
        evidence_count = int(qc_summary.get("clean_execution_count") or qc_summary.get("execution_count") or 0)
        avg_overall = self._as_float(qc_summary.get("avg_overall_score"))
        avg_payoff = self._as_float(qc_summary.get("avg_payoff_quality"))
        hold_or_reject = self._as_float(qc_summary.get("recent_hold_or_reject_rate"))
        qc_confidence = self._as_float(
            ((qc_summary.get("qc_analysis") or {}).get("confidence_summary") or {}).get("adjusted_confidence")
        )
        calibrated_confidence = self._as_float(confidence_calibration.confidence)
        evidence_confidence = min(calibrated_confidence, max(self._confidence(evidence_count), qc_confidence))
        contamination_impact = {
            "contamination_rate": self._as_float(contamination_summary.get("contamination_rate")),
            "noise_rate": self._as_float(contamination_summary.get("noise_rate")),
            "weak_signal_rate": self._as_float(contamination_summary.get("weak_signal_rate")),
            "insufficient_rate": self._as_float(contamination_summary.get("insufficient_rate")),
            "dominant_problem": str(contamination_summary.get("dominant_problem") or "none"),
            "policy_safe": bool(contamination_summary.get("policy_safe", False)),
            "confidence_penalty": self._as_float(contamination_summary.get("confidence_penalty")),
        }

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

        hook_signal = LearningPolicySignal(
            value=recommended_hook,
            confidence=evidence_confidence,
            evidence_count=evidence_count,
        )
        duration_signal = LearningPolicySignal(
            value=target_duration_range,
            confidence=evidence_confidence,
            evidence_count=evidence_count,
        )
        payoff_signal = LearningPolicySignal(
            value=payoff_specificity,
            confidence=round(min(calibrated_confidence, max(evidence_confidence, avg_payoff * 0.75)), 4),
            evidence_count=evidence_count,
        )
        risk_signal = LearningPolicySignal(
            value=risk_hint,
            confidence=round(min(calibrated_confidence, max(evidence_confidence, min(1.0, hold_or_reject + 0.25))), 4),
            evidence_count=evidence_count,
        )
        variation_signal = LearningPolicySignal(
            value=variation_hint,
            confidence=round(min(calibrated_confidence, variation_confidence), 4),
            evidence_count=variation_evidence,
        )
        strategy_pressure = self._build_strategy_pressure(
            hook_signal=hook_signal,
            duration_signal=duration_signal,
            payoff_signal=payoff_signal,
            risk_signal=risk_signal,
            variation_signal=variation_signal,
            confidence_calibration=confidence_calibration,
            confidence_inputs=confidence_inputs,
            contamination_impact=contamination_impact,
            qc_summary=qc_summary,
        )

        return LearningPolicy(
            hook_type_bias=hook_signal,
            duration_bias=duration_signal,
            payoff_specificity_bias=payoff_signal,
            risk_adjustment_hint=risk_signal,
            variation_tolerance_hint=variation_signal,
            strategy_pressure=strategy_pressure,
            confidence_summary={
                "confidence": calibrated_confidence,
                "policy_strength": confidence_calibration.policy_strength,
                "confidence_components": dict(confidence_calibration.confidence_components),
                "confidence_rationale": dict(confidence_calibration.confidence_rationale),
                "evidence_origin_mix": dict(confidence_calibration.evidence_origin_mix),
                "controlled_validation_dominance": confidence_calibration.controlled_validation_dominance,
                "real_runtime_support": confidence_calibration.real_runtime_support,
                "bootstrap_bias_risk": confidence_calibration.bootstrap_bias_risk,
                "temporal_pattern_type": confidence_calibration.confidence_rationale.get("temporal_pattern_type"),
                "contamination_impact": contamination_impact,
                "noise_impact": {
                    "noise_rate": contamination_impact["noise_rate"],
                    "dominant_problem": contamination_impact["dominant_problem"],
                    "policy_safe": contamination_impact["policy_safe"],
                },
                "clean_execution_count": evidence_count,
                "avg_overall_score": avg_overall,
                "avg_payoff_quality": avg_payoff,
                "qc_adjusted_confidence": qc_confidence,
                "fallback_contamination_rate": self._as_float(qc_summary.get("fallback_contamination_rate")),
                "strategy_pressure": strategy_pressure.to_dict(),
            },
            policy_trace={
                "recent_hold_or_reject_rate": hold_or_reject,
                "variation_source": variation_hint,
                "pattern_findings_count": len(pattern_findings),
                "qc_analysis": (qc_summary.get("qc_analysis") or {}).get("confidence_summary", {}),
                "confidence_calibration": {
                    "sample_size": confidence_calibration.confidence_rationale["sample_size"],
                    "clean_sample_size": confidence_calibration.confidence_rationale["clean_sample_size"],
                    "contamination_rate": confidence_calibration.confidence_rationale["contamination_rate"],
                    "signal_consistency": confidence_inputs["signal_consistency"],
                    "signal_strength": confidence_inputs["signal_strength"],
                    "bootstrap_bias_risk": confidence_calibration.bootstrap_bias_risk,
                    "controlled_validation_dominance": confidence_calibration.controlled_validation_dominance,
                    "temporal_pattern_type": confidence_inputs["temporal_pattern_type"],
                    "policy_strength": confidence_calibration.policy_strength,
                    "final_confidence": calibrated_confidence,
                },
                "contamination_analysis": contamination_impact,
                "strategy_pressure": strategy_pressure.to_dict(),
            },
        )

    def _build_strategy_pressure(
        self,
        *,
        hook_signal: LearningPolicySignal,
        duration_signal: LearningPolicySignal,
        payoff_signal: LearningPolicySignal,
        risk_signal: LearningPolicySignal,
        variation_signal: LearningPolicySignal,
        confidence_calibration: ConfidenceCalibration,
        confidence_inputs: dict[str, Any],
        contamination_impact: dict[str, Any],
        qc_summary: dict[str, Any],
    ) -> LearningStrategyPressure:
        confidence = self._as_float(confidence_calibration.confidence)
        policy_strength = str(confidence_calibration.policy_strength or "weak")
        temporal_pattern_type = str(confidence_inputs.get("temporal_pattern_type") or "volatile")
        policy_safe = bool(contamination_impact.get("policy_safe", False))
        contamination_rate = self._as_float(contamination_impact.get("contamination_rate"))
        noise_rate = self._as_float(contamination_impact.get("noise_rate"))
        weak_signal_rate = self._as_float(contamination_impact.get("weak_signal_rate"))
        insufficient_rate = self._as_float(contamination_impact.get("insufficient_rate"))
        clean_sample_size = int(confidence_calibration.confidence_rationale.get("clean_sample_size") or 0)
        evidence_count = int(confidence_calibration.confidence_rationale.get("sample_size") or 0)
        raw_dominant_problem = str(contamination_impact.get("dominant_problem") or "none")
        dominant_problem = "insufficient" if clean_sample_size < 3 and raw_dominant_problem == "none" else raw_dominant_problem

        unsafe_pressure = (
            not policy_safe
            or clean_sample_size < 5
            or contamination_rate > 0.4
            or noise_rate > 0.35
            or insufficient_rate > 0.4
            or dominant_problem in {"contamination", "noise", "insufficient"}
        )
        strong_allowed = (
            policy_strength == "strong"
            and confidence >= 0.7
            and policy_safe
            and clean_sample_size >= 10
            and temporal_pattern_type == "durable_pattern"
            and dominant_problem in {"none", "weak_signal"}
            and contamination_rate <= 0.2
            and noise_rate <= 0.2
        )
        if strong_allowed:
            pressure_mode = "strong_bias"
        elif policy_strength == "medium" and not unsafe_pressure and confidence >= 0.35:
            pressure_mode = "medium_bias"
        else:
            pressure_mode = "weak_bias"

        no_meaningful_pressure = clean_sample_size < 3 or dominant_problem == "insufficient"
        target_confidence_cap = 0.34 if pressure_mode == "weak_bias" else confidence
        targets: list[LearningStrategyPressureTarget] = []
        if not no_meaningful_pressure:
            avg_overall = self._as_float(qc_summary.get("avg_overall_score"))
            avg_payoff = self._as_float(qc_summary.get("avg_payoff_quality"))
            hold_or_reject = self._as_float(qc_summary.get("recent_hold_or_reject_rate"))
            targets = self._strategy_pressure_targets(
                signals={
                    "hook_type": hook_signal,
                    "duration": duration_signal,
                    "payoff_specificity": payoff_signal,
                    "risk_adjustment": risk_signal,
                    "variation_tolerance": variation_signal,
                },
                confidence_cap=target_confidence_cap,
                temporal_pattern_type=temporal_pattern_type,
                avg_overall=avg_overall,
                avg_payoff=avg_payoff,
                hold_or_reject=hold_or_reject,
                clean_sample_size=clean_sample_size,
                policy_safe=policy_safe,
            )

        origin_summary = {
            "confidence": confidence,
            "policy_strength": policy_strength,
            "temporal_pattern_type": temporal_pattern_type,
            "contamination_rate": contamination_rate,
            "noise_rate": noise_rate,
            "weak_signal_rate": weak_signal_rate,
            "insufficient_rate": insufficient_rate,
            "dominant_problem": dominant_problem,
            "policy_safe": policy_safe,
            "clean_sample_size": clean_sample_size,
            "evidence_count": evidence_count,
            "pressure_capped": pressure_mode == "weak_bias" and policy_strength != "weak",
        }
        return LearningStrategyPressure(
            pressure_mode=pressure_mode,
            pressure_targets=targets,
            confidence=round(confidence, 4),
            bounded=True,
            strategy_influence_mode="bounded",
            strategy_override_allowed=True,
            higher_authority_constraints_apply=True,
            pressure_origin_summary=origin_summary,
        )

    def _strategy_pressure_targets(
        self,
        *,
        signals: dict[str, LearningPolicySignal],
        confidence_cap: float,
        temporal_pattern_type: str,
        avg_overall: float,
        avg_payoff: float,
        hold_or_reject: float,
        clean_sample_size: int,
        policy_safe: bool,
    ) -> list[LearningStrategyPressureTarget]:
        targets: list[LearningStrategyPressureTarget] = []
        for field_name, signal in signals.items():
            if not signal.value or signal.evidence_count <= 0:
                continue
            target_confidence = round(min(self._as_float(signal.confidence), confidence_cap), 4)
            if target_confidence <= 0.0:
                continue
            targets.append(
                LearningStrategyPressureTarget(
                    field=field_name,
                    value=signal.value,
                    confidence=target_confidence,
                    evidence_count=int(signal.evidence_count),
                    rationale=self._strategy_pressure_rationale(
                        field_name=field_name,
                        value=signal.value,
                        temporal_pattern_type=temporal_pattern_type,
                        avg_overall=avg_overall,
                        avg_payoff=avg_payoff,
                        hold_or_reject=hold_or_reject,
                        clean_sample_size=clean_sample_size,
                        policy_safe=policy_safe,
                    ),
                )
            )
        return targets

    def _strategy_pressure_rationale(
        self,
        *,
        field_name: str,
        value: str,
        temporal_pattern_type: str,
        avg_overall: float,
        avg_payoff: float,
        hold_or_reject: float,
        clean_sample_size: int,
        policy_safe: bool,
    ) -> str:
        if field_name == "duration":
            return (
                f"Clean evidence count {clean_sample_size} supports duration '{value}' with "
                f"overall score {avg_overall:.2f} under temporal pattern '{temporal_pattern_type}'; "
                f"Strategy remains authoritative and policy_safe={policy_safe}."
            )
        if field_name == "payoff_specificity":
            return (
                f"Payoff quality average {avg_payoff:.2f} supports payoff specificity '{value}' "
                f"from bounded Learning evidence; Strategy may soften or ignore this pressure."
            )
        if field_name == "risk_adjustment":
            return (
                f"Hold/reject rate {hold_or_reject:.2f} and overall score {avg_overall:.2f} justify "
                f"risk adjustment '{value}' as bounded pressure, not enforcement."
            )
        if field_name == "variation_tolerance":
            return (
                f"Pattern evidence supports variation tolerance '{value}' while preserving Novelty and "
                f"Strategy ownership; temporal pattern is '{temporal_pattern_type}'."
            )
        return (
            f"Clean evidence count {clean_sample_size} supports {field_name} '{value}' under temporal "
            f"pattern '{temporal_pattern_type}'; this is bounded Learning pressure only."
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
