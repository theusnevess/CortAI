from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


QC_EVIDENCE_SCORING_VERSION = "qc_confidence_evidence_v2_6"


TECHNICAL_FAILURE_CODES = {
    "QC_RENDER_JOB_ID_MISSING",
    "QC_VIDEO_MISSING",
    "QC_AUDIO_MISSING",
    "QC_METADATA_MISSING",
    "QC_DURATION_BELOW_MINIMUM",
    "QC_SUBTITLE_CUES_INVALID",
    "QC_EMPTY_CUE_TEXT",
    "QC_RESOLUTION_INVALID",
    "QC_AUDIO_STREAM_MISSING",
    "QC_INTERNAL_ERROR",
}

PERCEPTUAL_FAILURE_CODES = {
    "QC_GLYPH_BROKEN",
    "QC_PAYOFF_TOO_DARK",
}

PRODUCT_FAILURE_CODES = {
    "QC_HOOK_QUALITY_FAIL",
    "QC_PAYOFF_QUALITY_FAIL",
    "QC_PUBLISHABILITY_FAIL",
    "QC_OVERALL_SCORE_FAIL",
    "QC_HOOK_QUALITY_BORDERLINE",
    "QC_PAYOFF_QUALITY_BORDERLINE",
    "QC_PUBLISHABILITY_HOLD",
    "QC_OVERALL_SCORE_BORDERLINE",
}


@dataclass(frozen=True)
class VideoQcScoreEvidence:
    score_key: str
    score: float
    level: str
    evidence_source: str
    reason_code: str
    rationale: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VideoQcEvidenceScoring:
    scoring_version: str
    status: str
    publishable: bool
    decision_rule_applied: str
    failure_categories: dict[str, list[str]]
    score_evidence: dict[str, VideoQcScoreEvidence]
    product_signal_evidence: dict[str, Any]
    dominant_reason_codes: list[str]
    decision_rationale: dict[str, Any]
    evidence_boundary_statement: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["score_evidence"] = {
            key: value.to_dict()
            for key, value in self.score_evidence.items()
        }
        return payload


@dataclass(frozen=True)
class VideoQcConfidenceCalibration:
    confidence: float
    confidence_level: str
    confidence_components: dict[str, float]
    confidence_rationale: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VideoQcConfidenceEvidenceResult:
    qc_evidence_scoring: VideoQcEvidenceScoring
    confidence_calibration: VideoQcConfidenceCalibration

    def to_dict(self) -> dict[str, Any]:
        return {
            "qc_evidence_scoring": self.qc_evidence_scoring.to_dict(),
            "confidence_calibration": self.confidence_calibration.to_dict(),
        }


@dataclass(frozen=True)
class VideoQcConfidenceEvidenceEvaluator:
    """Audit-only evidence and confidence layer for existing QC decisions."""

    def evaluate(
        self,
        *,
        status: str,
        publishable: bool,
        hard_failures: list[str],
        soft_failures: list[str],
        product_vetoes: list[str],
        score_summary: dict[str, float],
        product_signals: dict[str, Any],
        qc_input_governance: dict[str, Any],
        details: dict[str, Any],
    ) -> VideoQcConfidenceEvidenceResult:
        unique_hard = list(dict.fromkeys(hard_failures))
        unique_soft = list(dict.fromkeys(soft_failures))
        unique_vetoes = list(dict.fromkeys(product_vetoes))
        all_reason_codes = [*unique_hard, *unique_vetoes, *unique_soft]

        evidence_scoring = VideoQcEvidenceScoring(
            scoring_version=QC_EVIDENCE_SCORING_VERSION,
            status=status,
            publishable=publishable,
            decision_rule_applied=self._decision_rule(status=status, hard_failures=unique_hard, product_vetoes=unique_vetoes, soft_failures=unique_soft),
            failure_categories=self._failure_categories(unique_hard, unique_vetoes, unique_soft, details=details),
            score_evidence=self._score_evidence(score_summary=score_summary, qc_input_governance=qc_input_governance, details=details),
            product_signal_evidence=self._product_signal_evidence(product_signals=product_signals, details=details),
            dominant_reason_codes=all_reason_codes,
            decision_rationale=self._decision_rationale(
                status=status,
                publishable=publishable,
                hard_failures=unique_hard,
                product_vetoes=unique_vetoes,
                soft_failures=unique_soft,
                product_signals=product_signals,
            ),
            evidence_boundary_statement="QC evidence scoring explains the existing decision; it does not change thresholds or publishability.",
        )
        confidence = self._confidence(
            status=status,
            publishable=publishable,
            hard_failures=unique_hard,
            soft_failures=unique_soft,
            product_vetoes=unique_vetoes,
            score_summary=score_summary,
            product_signals=product_signals,
            qc_input_governance=qc_input_governance,
            details=details,
        )
        return VideoQcConfidenceEvidenceResult(
            qc_evidence_scoring=evidence_scoring,
            confidence_calibration=confidence,
        )

    def _decision_rule(self, *, status: str, hard_failures: list[str], product_vetoes: list[str], soft_failures: list[str]) -> str:
        if status == "REJECT" and hard_failures:
            return "hard_failure_reject"
        if status == "REJECT" and product_vetoes:
            return "product_veto_reject"
        if status == "HOLD" and soft_failures:
            return "soft_failure_hold"
        if status == "APPROVE":
            return "clean_approve"
        return "inconsistent_or_unclassified"

    def _failure_categories(
        self,
        hard_failures: list[str],
        product_vetoes: list[str],
        soft_failures: list[str],
        *,
        details: dict[str, Any],
    ) -> dict[str, list[str]]:
        technical = [code for code in hard_failures if code in TECHNICAL_FAILURE_CODES]
        perceptual = [code for code in hard_failures if code in PERCEPTUAL_FAILURE_CODES]
        product = [code for code in [*product_vetoes, *soft_failures] if code in PRODUCT_FAILURE_CODES]
        environment = []
        if details.get("probe_mode") == "metadata_fallback":
            environment.append("QC_METADATA_FALLBACK_PROBE_USED")
        if details.get("probe_mode") == "unavailable":
            environment.append("QC_MEDIA_PROBE_UNAVAILABLE")
        unknown = [
            code
            for code in [*hard_failures, *product_vetoes, *soft_failures]
            if code not in {*TECHNICAL_FAILURE_CODES, *PERCEPTUAL_FAILURE_CODES, *PRODUCT_FAILURE_CODES}
        ]
        return {
            "technical_failures": technical,
            "perceptual_failures": perceptual,
            "product_failures": product,
            "environment_limitations": environment,
            "unknown_failures": unknown,
        }

    def _score_evidence(
        self,
        *,
        score_summary: dict[str, float],
        qc_input_governance: dict[str, Any],
        details: dict[str, Any],
    ) -> dict[str, VideoQcScoreEvidence]:
        evidence: dict[str, VideoQcScoreEvidence] = {}
        for score_key in sorted(score_summary):
            score = self._float(score_summary.get(score_key))
            evidence[score_key] = VideoQcScoreEvidence(
                score_key=score_key,
                score=score,
                level=self._level(score),
                evidence_source=self._score_source(score_key, qc_input_governance=qc_input_governance, details=details),
                reason_code=f"{score_key.upper()}_EVIDENCE_RECORDED",
                rationale=self._score_rationale(score_key, score=score, qc_input_governance=qc_input_governance, details=details),
            )
        return evidence

    def _product_signal_evidence(self, *, product_signals: dict[str, Any], details: dict[str, Any]) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        for key in sorted(product_signals):
            value = product_signals.get(key)
            entry: dict[str, Any] = {
                "value": value,
                "evidence_source": "metadata_and_score_summary",
                "rationale": "Existing QC product signal was recorded for audit; no score math was changed.",
            }
            if isinstance(value, (int, float)):
                entry["level"] = self._level(float(value))
            elif isinstance(value, bool):
                entry["level"] = "pass" if value else "fail"
            payload[key] = entry
        if "probe_mode" in details:
            payload["media_probe_mode"] = {
                "value": details.get("probe_mode"),
                "evidence_source": "media_probe_or_metadata_fallback",
                "rationale": "Probe mode qualifies the strength of media evidence.",
            }
        return payload

    def _decision_rationale(
        self,
        *,
        status: str,
        publishable: bool,
        hard_failures: list[str],
        product_vetoes: list[str],
        soft_failures: list[str],
        product_signals: dict[str, Any],
    ) -> dict[str, Any]:
        rationale: list[str]
        if status == "APPROVE":
            rationale = ["APPROVE because no hard failures, product vetoes, or soft failures were emitted by existing QC logic."]
        elif status == "HOLD":
            rationale = ["HOLD because existing QC logic emitted soft product-quality failures without hard technical failures."]
        elif hard_failures:
            rationale = ["REJECT because existing QC logic emitted one or more hard technical/perceptual failures."]
        elif product_vetoes:
            rationale = ["REJECT because existing QC logic emitted one or more product vetoes."]
        else:
            rationale = ["Decision status is emitted by existing QC logic; rationale is limited by available reason codes."]
        return {
            "status": status,
            "publishable": publishable,
            "hard_failures": hard_failures,
            "soft_failures": soft_failures,
            "product_vetoes": product_vetoes,
            "publishability_signal": product_signals.get("publishable"),
            "rationale": rationale,
        }

    def _confidence(
        self,
        *,
        status: str,
        publishable: bool,
        hard_failures: list[str],
        soft_failures: list[str],
        product_vetoes: list[str],
        score_summary: dict[str, float],
        product_signals: dict[str, Any],
        qc_input_governance: dict[str, Any],
        details: dict[str, Any],
    ) -> VideoQcConfidenceCalibration:
        components = {
            "artifact_evidence_completeness": self._artifact_evidence_completeness(qc_input_governance),
            "technical_validation_completeness": self._technical_validation_completeness(qc_input_governance=qc_input_governance, details=details),
            "product_signal_coverage": self._product_signal_coverage(score_summary=score_summary, product_signals=product_signals),
            "trace_evidence_quality": self._trace_evidence_quality(qc_input_governance),
            "media_probe_quality": self._media_probe_quality(details),
            "decision_consistency": self._decision_consistency(
                status=status,
                publishable=publishable,
                hard_failures=hard_failures,
                product_vetoes=product_vetoes,
                soft_failures=soft_failures,
                product_signals=product_signals,
            ),
            "fallback_environment_penalty": self._fallback_environment_penalty(qc_input_governance=qc_input_governance, details=details),
        }
        weighted = (
            (components["artifact_evidence_completeness"] * 0.2)
            + (components["technical_validation_completeness"] * 0.15)
            + (components["product_signal_coverage"] * 0.15)
            + (components["trace_evidence_quality"] * 0.15)
            + (components["media_probe_quality"] * 0.15)
            + (components["decision_consistency"] * 0.2)
            - components["fallback_environment_penalty"]
        )
        penalties = self._penalties(
            status=status,
            hard_failures=hard_failures,
            soft_failures=soft_failures,
            qc_input_governance=qc_input_governance,
            details=details,
        )
        for penalty in penalties:
            weighted -= self._float(penalty.get("amount"))
        confidence = self._apply_caps(
            value=weighted,
            status=status,
            hard_failures=hard_failures,
            soft_failures=soft_failures,
            qc_input_governance=qc_input_governance,
            details=details,
        )
        confidence = self._clamp(confidence)
        return VideoQcConfidenceCalibration(
            confidence=confidence,
            confidence_level=self._confidence_level(confidence),
            confidence_components={key: self._clamp(value) for key, value in components.items()},
            confidence_rationale={
                "confidence_meaning": "trust_in_qc_decision",
                "penalties": penalties,
                "boundary_statement": "QC confidence is not performance prediction.",
                "rationale": self._confidence_rationale(status=status, confidence=confidence, details=details, penalties=penalties),
            },
        )

    def _artifact_evidence_completeness(self, governance: dict[str, Any]) -> float:
        required = ["render_job_id", "video_artifact", "audio_artifact", "metadata_artifact"]
        signals = self._signals_by_key(governance)
        total = 0.0
        for key in required:
            signal = signals.get(key, {})
            status = signal.get("status")
            if status == "available":
                total += 1.0
            elif status in {"degraded", "environment_dependent"}:
                total += 0.45
        return total / len(required)

    def _technical_validation_completeness(self, *, qc_input_governance: dict[str, Any], details: dict[str, Any]) -> float:
        metadata_loaded = bool(qc_input_governance.get("artifact_summary", {}).get("metadata_loaded"))
        probe_mode = str(details.get("probe_mode") or qc_input_governance.get("environment_summary", {}).get("media_probe_mode") or "unavailable")
        if metadata_loaded and probe_mode == "ffprobe":
            return 1.0
        if metadata_loaded and probe_mode == "metadata_fallback":
            return 0.75
        if metadata_loaded:
            return 0.65
        return 0.35

    def _product_signal_coverage(self, *, score_summary: dict[str, float], product_signals: dict[str, Any]) -> float:
        expected_scores = {"script_quality", "voice_quality", "asset_quality", "edit_quality", "product_quality", "overall_score"}
        expected_signals = {"hook_quality", "payoff_quality", "publishability_signal", "publishable", "setup_luma_ok"}
        score_count = len(expected_scores.intersection(score_summary))
        signal_count = len(expected_signals.intersection(product_signals))
        return ((score_count / len(expected_scores)) * 0.55) + ((signal_count / len(expected_signals)) * 0.45)

    def _trace_evidence_quality(self, governance: dict[str, Any]) -> float:
        signals = self._signals_by_key(governance)
        trace_keys = ["tts_trace", "visual_trace", "edit_trace"]
        total = 0.0
        for key in trace_keys:
            status = signals.get(key, {}).get("status")
            if status == "available":
                total += 1.0
            elif status == "ignored":
                total += 0.8
            elif status in {"degraded", "environment_dependent"}:
                total += 0.45
            elif status == "missing":
                total += 0.15
        return total / len(trace_keys)

    def _media_probe_quality(self, details: dict[str, Any]) -> float:
        probe_mode = str(details.get("probe_mode") or "unavailable")
        if probe_mode == "ffprobe":
            return 1.0
        if probe_mode == "metadata_fallback":
            return 0.65
        return 0.25

    def _decision_consistency(
        self,
        *,
        status: str,
        publishable: bool,
        hard_failures: list[str],
        product_vetoes: list[str],
        soft_failures: list[str],
        product_signals: dict[str, Any],
    ) -> float:
        if status == "APPROVE":
            return 1.0 if not hard_failures and not product_vetoes and not soft_failures and publishable and bool(product_signals.get("publishable")) else 0.0
        if status == "HOLD":
            return 1.0 if not hard_failures and not product_vetoes and bool(soft_failures) and not publishable else 0.0
        if status == "REJECT":
            return 1.0 if (hard_failures or product_vetoes) and not publishable else 0.0
        return 0.0

    def _fallback_environment_penalty(self, *, qc_input_governance: dict[str, Any], details: dict[str, Any]) -> float:
        penalty = 0.0
        if details.get("probe_mode") == "metadata_fallback":
            penalty += 0.08
        if details.get("probe_mode") == "unavailable":
            penalty += 0.16
        if qc_input_governance.get("environment_dependent_inputs"):
            penalty += 0.04
        return min(0.3, penalty)

    def _penalties(
        self,
        *,
        status: str,
        hard_failures: list[str],
        soft_failures: list[str],
        qc_input_governance: dict[str, Any],
        details: dict[str, Any],
    ) -> list[dict[str, Any]]:
        penalties: list[dict[str, Any]] = []
        missing_required = [
            key
            for key in qc_input_governance.get("missing_inputs", [])
            if key in {"render_job_id", "video_artifact", "audio_artifact", "metadata_artifact"}
        ]
        if missing_required:
            penalties.append({
                "reason_code": "QC_REQUIRED_ARTIFACT_EVIDENCE_MISSING",
                "amount": 0.12,
                "affected_inputs": missing_required,
            })
        missing_traces = [
            key
            for key in qc_input_governance.get("missing_inputs", [])
            if key in {"tts_trace", "visual_trace", "edit_trace"}
        ]
        if missing_traces:
            penalties.append({
                "reason_code": "QC_OPTIONAL_UPSTREAM_TRACE_MISSING",
                "amount": min(0.09, 0.03 * len(missing_traces)),
                "affected_inputs": missing_traces,
            })
        if details.get("probe_mode") == "metadata_fallback":
            penalties.append({
                "reason_code": "QC_METADATA_FALLBACK_LIMITS_MEDIA_EVIDENCE",
                "amount": 0.08,
            })
        if status == "HOLD" and soft_failures:
            penalties.append({
                "reason_code": "QC_HOLD_IS_BORDERLINE_DECISION",
                "amount": 0.06,
                "affected_reason_codes": soft_failures,
            })
        if "QC_INTERNAL_ERROR" in hard_failures:
            penalties.append({
                "reason_code": "QC_INTERNAL_ERROR_LIMITS_CONFIDENCE",
                "amount": 0.35,
            })
        return penalties

    def _apply_caps(
        self,
        *,
        value: float,
        status: str,
        hard_failures: list[str],
        soft_failures: list[str],
        qc_input_governance: dict[str, Any],
        details: dict[str, Any],
    ) -> float:
        capped = value
        if "QC_INTERNAL_ERROR" in hard_failures:
            capped = min(capped, 0.2)
        if not qc_input_governance.get("policy_respected", True):
            capped = min(capped, 0.65)
        if "metadata_artifact" in qc_input_governance.get("missing_inputs", []):
            capped = min(capped, 0.58)
        if details.get("probe_mode") == "metadata_fallback":
            capped = min(capped, 0.74)
        if status == "HOLD" or soft_failures:
            capped = min(capped, 0.72)
        missing_traces = [
            key
            for key in qc_input_governance.get("missing_inputs", [])
            if key in {"tts_trace", "visual_trace", "edit_trace"}
        ]
        if len(missing_traces) >= 2:
            capped = min(capped, 0.82)
        return capped

    def _confidence_rationale(self, *, status: str, confidence: float, details: dict[str, Any], penalties: list[dict[str, Any]]) -> list[str]:
        rationale = [
            f"Confidence measures trust in the emitted {status} decision, not content performance.",
            "Existing QC thresholds and publishability logic were not changed.",
        ]
        if details.get("probe_mode") == "metadata_fallback":
            rationale.append("Metadata fallback reduces trust because full media probe evidence was unavailable.")
        if penalties:
            rationale.append("Confidence was reduced by explicit evidence limitations.")
        if confidence >= 0.75:
            rationale.append("High confidence requires coherent artifacts, product signals, probe evidence, and decision consistency.")
        return rationale

    def _score_source(self, score_key: str, *, qc_input_governance: dict[str, Any], details: dict[str, Any]) -> str:
        if score_key == "script_quality":
            return "script_text_or_subtitle_cues"
        if score_key == "voice_quality":
            return "audio_probe_and_tts_trace"
        if score_key == "asset_quality":
            return "metadata_luma_proxy"
        if score_key == "edit_quality":
            return "subtitle_cues_duration_and_edit_trace"
        if score_key in {"product_quality", "overall_score"}:
            return "deterministic_score_summary"
        return "existing_qc_score_summary"

    def _score_rationale(self, score_key: str, *, score: float, qc_input_governance: dict[str, Any], details: dict[str, Any]) -> list[str]:
        rationale = [f"{score_key} is an existing deterministic QC proxy recorded without changing scoring math."]
        if score_key == "voice_quality" and "tts_trace" in qc_input_governance.get("missing_inputs", []):
            rationale.append("Missing TTS trace limits voice evidence even when audio artifact exists.")
        if score_key == "asset_quality":
            rationale.append("Asset quality uses metadata luma proxy only; no pixel-level or ML visual validation is claimed.")
        if score_key == "edit_quality" and "edit_trace" in qc_input_governance.get("missing_inputs", []):
            rationale.append("Missing edit trace limits edit evidence; subtitle metadata remains the primary proxy.")
        if details.get("probe_mode") == "metadata_fallback":
            rationale.append("Media evidence was partially fallback-derived from metadata.")
        return rationale

    def _signals_by_key(self, governance: dict[str, Any]) -> dict[str, dict[str, Any]]:
        return {
            str(signal.get("input_key")): signal
            for signal in governance.get("input_signals", [])
            if isinstance(signal, dict)
        }

    def _level(self, value: float) -> str:
        if value >= 0.74:
            return "high"
        if value >= 0.5:
            return "medium"
        return "low"

    def _confidence_level(self, value: float) -> str:
        if value >= 0.75:
            return "high"
        if value >= 0.5:
            return "medium"
        return "low"

    def _float(self, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _clamp(self, value: float) -> float:
        return max(0.0, min(1.0, round(float(value), 4)))
