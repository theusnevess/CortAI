from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.content.pipeline.render import MIN_VIDEO_DURATION_S
from app.creative.agents.video_qc.confidence_evidence import VideoQcConfidenceEvidenceEvaluator
from app.creative.agents.video_qc.decision_semantics import VideoQcDecisionSemanticsEvaluator
from app.creative.agents.video_qc.input_governance import VideoQcInputGovernanceEvaluator
from app.creative.agents.video_qc.models import VideoQcDecision, VideoQcInput, VideoQcResult
from app.creative.agents.video_qc.trace_auditability import VideoQcTraceBuilder


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _clamp_score(value: float) -> float:
    return max(0.0, min(1.0, round(value, 4)))


@dataclass
class VideoQcAgentService:
    def evaluate(
        self,
        *,
        qc_input: VideoQcInput | None = None,
        render_job_id: str | None = None,
        artifacts: object | None = None,
        base_dir: Path | None = None,
    ) -> VideoQcResult:
        try:
            resolved_input = qc_input or self._build_input(
                render_job_id=render_job_id or "",
                artifacts=artifacts,
                base_dir=base_dir or Path("OUT/content"),
            )
            return self._evaluate(qc_input=resolved_input)
        except Exception as exc:  # noqa: BLE001
            checked_at = _now_iso()
            fallback_input = qc_input or VideoQcInput(
                render_job_id=render_job_id or "",
                video_path="",
                audio_path="",
                metadata_path=None,
            )
            input_governance = VideoQcInputGovernanceEvaluator().evaluate(
                qc_input=fallback_input,
                probe={"width": None, "height": None, "has_audio": False, "probe_mode": "unavailable"},
                metadata_loaded=False,
                hard_failures=["QC_INTERNAL_ERROR"],
            ).to_dict()
            decision = VideoQcDecision(
                status="REJECT",
                publishable=False,
                hard_failures=["QC_INTERNAL_ERROR"],
                score_summary={"overall_score": 0.0},
                product_signals={"publishable": False},
                decision_trace={
                    "stage": "exception_handler",
                    "qc_input_governance": input_governance,
                },
                checked_at=checked_at,
            )
            confidence_evidence = VideoQcConfidenceEvidenceEvaluator().evaluate(
                status=decision.status,
                publishable=decision.publishable,
                hard_failures=decision.hard_failures,
                soft_failures=decision.soft_failures,
                product_vetoes=decision.product_vetoes,
                score_summary=decision.score_summary,
                product_signals=decision.product_signals,
                qc_input_governance=input_governance,
                details={"probe_mode": "unavailable", "qc_input_governance": input_governance},
            ).to_dict()
            decision_semantics = VideoQcDecisionSemanticsEvaluator().evaluate(
                status=decision.status,
                publishable=decision.publishable,
                hard_failures=decision.hard_failures,
                soft_failures=decision.soft_failures,
                product_vetoes=decision.product_vetoes,
                score_summary=decision.score_summary,
                product_signals=decision.product_signals,
                qc_input_governance=input_governance,
                qc_evidence_scoring=confidence_evidence["qc_evidence_scoring"],
                confidence_calibration=confidence_evidence["confidence_calibration"],
                details={"probe_mode": "unavailable", "qc_input_governance": input_governance},
            ).to_dict()
            qc_trace = VideoQcTraceBuilder().build(
                status=decision.status,
                publishable=decision.publishable,
                reasons=["QC_INTERNAL_ERROR"],
                qc_input_governance=input_governance,
                qc_evidence_scoring=confidence_evidence["qc_evidence_scoring"],
                confidence_calibration=confidence_evidence["confidence_calibration"],
                decision_semantics=decision_semantics,
                details={"probe_mode": "unavailable", "qc_input_governance": input_governance},
            )
            decision = replace(
                decision,
                decision_trace={
                    **decision.decision_trace,
                    "qc_evidence_scoring": confidence_evidence["qc_evidence_scoring"],
                    "confidence_calibration": confidence_evidence["confidence_calibration"],
                    "decision_semantics": decision_semantics,
                    "qc_trace": qc_trace,
                },
            )
            return VideoQcResult(
                decision=decision,
                status="REJECT",
                reasons=["QC_INTERNAL_ERROR"],
                checked_at=checked_at,
                publishable=False,
                details={
                    "render_job_id": fallback_input.render_job_id,
                    "error": str(exc) or exc.__class__.__name__,
                    "qc_input_governance": input_governance,
                    "qc_evidence_scoring": confidence_evidence["qc_evidence_scoring"],
                    "confidence_calibration": confidence_evidence["confidence_calibration"],
                    "decision_semantics": decision_semantics,
                    "qc_trace": qc_trace,
                },
                qc_input_governance=input_governance,
                qc_evidence_scoring=confidence_evidence["qc_evidence_scoring"],
                decision_semantics=decision_semantics,
                qc_trace=qc_trace,
                confidence=confidence_evidence["confidence_calibration"]["confidence"],
                confidence_level=confidence_evidence["confidence_calibration"]["confidence_level"],
                confidence_components=confidence_evidence["confidence_calibration"]["confidence_components"],
                confidence_rationale=confidence_evidence["confidence_calibration"]["confidence_rationale"],
            )

    def _build_input(self, *, render_job_id: str, artifacts: object | None, base_dir: Path) -> VideoQcInput:
        if not isinstance(artifacts, dict):
            return VideoQcInput(render_job_id=render_job_id, video_path="", audio_path="", metadata_path=None)
        metadata_path = base_dir / "metadata" / f"{render_job_id}.json"
        return VideoQcInput(
            render_job_id=render_job_id,
            video_path=str(artifacts.get("video") or ""),
            audio_path=str(artifacts.get("audio") or ""),
            metadata_path=str(metadata_path) if metadata_path.exists() else None,
        )

    def _evaluate(self, *, qc_input: VideoQcInput) -> VideoQcResult:
        checked_at = _now_iso()
        details: dict[str, Any] = {
            "render_job_id": qc_input.render_job_id,
            "video_path": qc_input.video_path,
            "audio_path": qc_input.audio_path,
            "metadata_path": qc_input.metadata_path,
        }
        hard_failures: list[str] = []
        soft_failures: list[str] = []
        product_vetoes: list[str] = []

        video_path = Path(qc_input.video_path)
        audio_path = Path(qc_input.audio_path)
        metadata_path = Path(qc_input.metadata_path) if qc_input.metadata_path else None

        if not qc_input.render_job_id:
            hard_failures.append("QC_RENDER_JOB_ID_MISSING")
        if not qc_input.video_path:
            hard_failures.append("QC_VIDEO_MISSING")
        if not qc_input.audio_path:
            hard_failures.append("QC_AUDIO_MISSING")
        if not video_path.exists() or (video_path.exists() and video_path.stat().st_size == 0):
            hard_failures.append("QC_VIDEO_MISSING")
        if not audio_path.exists() or (audio_path.exists() and audio_path.stat().st_size == 0):
            hard_failures.append("QC_AUDIO_MISSING")
        if metadata_path is None or not metadata_path.exists():
            hard_failures.append("QC_METADATA_MISSING")

        metadata: dict[str, Any] = {}
        subtitle_cues: list[dict[str, Any]] = []
        render_duration = 0.0
        setup_luma = None
        payoff_luma = None
        probe: dict[str, Any] = {"width": None, "height": None, "has_audio": False, "probe_mode": "unavailable"}

        if not hard_failures:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            subtitle_cues = metadata.get("subtitle_cues", []) if isinstance(metadata.get("subtitle_cues"), list) else []
            render_duration = float(metadata.get("render_duration_s") or 0.0)
            setup_luma = metadata.get("setup_background_mean_luma")
            payoff_luma = metadata.get("payoff_background_mean_luma")
            details["render_duration_s"] = render_duration
            details["setup_background_mean_luma"] = setup_luma
            details["payoff_background_mean_luma"] = payoff_luma

            self._collect_metadata_failures(
                hard_failures=hard_failures,
                subtitle_cues=subtitle_cues,
                render_duration=render_duration,
                payoff_luma=payoff_luma,
            )

            probe = self._probe_video(video_path)
            if probe.get("probe_mode") == "unavailable":
                inferred = self._infer_dimensions_from_metadata(metadata)
                probe["width"] = inferred["width"]
                probe["height"] = inferred["height"]
                probe["has_audio"] = audio_path.exists() and audio_path.stat().st_size > 0
                probe["probe_mode"] = "metadata_fallback"
            details.update(probe)
            if probe.get("width") != 1080 or probe.get("height") != 1920:
                hard_failures.append("QC_RESOLUTION_INVALID")
            if not probe.get("has_audio"):
                hard_failures.append("QC_AUDIO_STREAM_MISSING")

        score_summary = self._build_score_summary(
            qc_input=qc_input,
            subtitle_cues=subtitle_cues,
            render_duration=render_duration,
            setup_luma=setup_luma,
            payoff_luma=payoff_luma,
            probe=probe,
        )
        product_signals = self._build_product_signals(
            subtitle_cues=subtitle_cues,
            render_duration=render_duration,
            setup_luma=setup_luma,
            payoff_luma=payoff_luma,
            score_summary=score_summary,
        )
        self._collect_soft_failures(
            soft_failures=soft_failures,
            product_vetoes=product_vetoes,
            score_summary=score_summary,
            product_signals=product_signals,
        )

        qc_input_governance = VideoQcInputGovernanceEvaluator().evaluate(
            qc_input=qc_input,
            probe=probe,
            metadata_loaded=bool(metadata),
            hard_failures=hard_failures,
        ).to_dict()

        decision = self._make_decision(
            checked_at=checked_at,
            hard_failures=hard_failures,
            soft_failures=soft_failures,
            product_vetoes=product_vetoes,
            score_summary=score_summary,
            product_signals=product_signals,
            qc_input_governance=qc_input_governance,
        )
        confidence_evidence = VideoQcConfidenceEvidenceEvaluator().evaluate(
            status=decision.status,
            publishable=decision.publishable,
            hard_failures=decision.hard_failures,
            soft_failures=decision.soft_failures,
            product_vetoes=decision.product_vetoes,
            score_summary=score_summary,
            product_signals=product_signals,
            qc_input_governance=qc_input_governance,
            details=details,
        ).to_dict()
        decision_semantics = VideoQcDecisionSemanticsEvaluator().evaluate(
            status=decision.status,
            publishable=decision.publishable,
            hard_failures=decision.hard_failures,
            soft_failures=decision.soft_failures,
            product_vetoes=decision.product_vetoes,
            score_summary=score_summary,
            product_signals=product_signals,
            qc_input_governance=qc_input_governance,
            qc_evidence_scoring=confidence_evidence["qc_evidence_scoring"],
            confidence_calibration=confidence_evidence["confidence_calibration"],
            details=details,
        ).to_dict()
        reasons = [*decision.hard_failures, *decision.product_vetoes, *decision.soft_failures]
        qc_trace = VideoQcTraceBuilder().build(
            status=decision.status,
            publishable=decision.publishable,
            reasons=reasons,
            qc_input_governance=qc_input_governance,
            qc_evidence_scoring=confidence_evidence["qc_evidence_scoring"],
            confidence_calibration=confidence_evidence["confidence_calibration"],
            decision_semantics=decision_semantics,
            details=details,
        )
        decision = replace(
            decision,
            decision_trace={
                **decision.decision_trace,
                "qc_evidence_scoring": confidence_evidence["qc_evidence_scoring"],
                "confidence_calibration": confidence_evidence["confidence_calibration"],
                "decision_semantics": decision_semantics,
                "qc_trace": qc_trace,
            },
        )
        details["score_summary"] = score_summary
        details["product_signals"] = product_signals
        details["qc_input_governance"] = qc_input_governance
        details["qc_evidence_scoring"] = confidence_evidence["qc_evidence_scoring"]
        details["confidence_calibration"] = confidence_evidence["confidence_calibration"]
        details["decision_semantics"] = decision_semantics
        details["qc_trace"] = qc_trace
        return VideoQcResult(
            decision=decision,
            status=decision.status,
            reasons=reasons,
            checked_at=checked_at,
            publishable=decision.publishable,
            details=details,
            qc_input_governance=qc_input_governance,
            qc_evidence_scoring=confidence_evidence["qc_evidence_scoring"],
            decision_semantics=decision_semantics,
            qc_trace=qc_trace,
            confidence=confidence_evidence["confidence_calibration"]["confidence"],
            confidence_level=confidence_evidence["confidence_calibration"]["confidence_level"],
            confidence_components=confidence_evidence["confidence_calibration"]["confidence_components"],
            confidence_rationale=confidence_evidence["confidence_calibration"]["confidence_rationale"],
        )

    def _collect_metadata_failures(
        self,
        *,
        hard_failures: list[str],
        subtitle_cues: list[dict[str, Any]],
        render_duration: float,
        payoff_luma: Any,
    ) -> None:
        if render_duration < MIN_VIDEO_DURATION_S:
            hard_failures.append("QC_DURATION_BELOW_MINIMUM")
        if len(subtitle_cues) < 3 or len(subtitle_cues) > 9:
            hard_failures.append("QC_SUBTITLE_CUES_INVALID")
            return
        for cue in subtitle_cues:
            text = str(cue.get("text") or "")
            if not text.strip():
                hard_failures.append("QC_EMPTY_CUE_TEXT")
                break
            if "\u25a1" in text or "\ufffd" in text:
                hard_failures.append("QC_GLYPH_BROKEN")
                break
        if isinstance(payoff_luma, (int, float)) and payoff_luma < 45:
            hard_failures.append("QC_PAYOFF_TOO_DARK")

    def _build_score_summary(
        self,
        *,
        qc_input: VideoQcInput,
        subtitle_cues: list[dict[str, Any]],
        render_duration: float,
        setup_luma: Any,
        payoff_luma: Any,
        probe: dict[str, Any],
    ) -> dict[str, float]:
        script_source = qc_input.script_text.strip() or " ".join(str(cue.get("text") or "") for cue in subtitle_cues)
        script_words = len(script_source.split())
        script_quality = 1.0 if script_words >= 8 else 0.55 if script_words >= 4 else 0.2

        trace_segment_count = len(qc_input.tts_trace.get("segment_durations", [])) if isinstance(qc_input.tts_trace, dict) else 0
        has_audio = bool(probe.get("has_audio"))
        voice_quality = 0.25
        if has_audio:
            voice_quality = 0.7
            if trace_segment_count >= 3:
                voice_quality = 0.9

        asset_quality = 0.55
        if isinstance(setup_luma, (int, float)) and isinstance(payoff_luma, (int, float)):
            asset_quality = 0.85 if 45 <= payoff_luma <= 185 and 35 <= setup_luma <= 185 else 0.65

        edit_quality = 0.45
        if len(subtitle_cues) >= 3 and render_duration >= MIN_VIDEO_DURATION_S:
            edit_quality = 0.8
            if qc_input.edit_trace:
                edit_quality = 0.9

        hook_quality = self._score_hook(subtitle_cues, render_duration)
        payoff_quality = self._score_payoff(subtitle_cues, render_duration, payoff_luma)
        publishability = self._score_publishability(hook_quality, payoff_quality, edit_quality, asset_quality)
        product_quality = _clamp_score((hook_quality * 0.4) + (payoff_quality * 0.4) + (publishability * 0.2))
        overall_score = _clamp_score(
            (script_quality * 0.15)
            + (voice_quality * 0.15)
            + (asset_quality * 0.2)
            + (edit_quality * 0.2)
            + (product_quality * 0.3)
        )
        return {
            "script_quality": script_quality,
            "voice_quality": voice_quality,
            "asset_quality": asset_quality,
            "edit_quality": edit_quality,
            "product_quality": product_quality,
            "overall_score": overall_score,
        }

    def _build_product_signals(
        self,
        *,
        subtitle_cues: list[dict[str, Any]],
        render_duration: float,
        setup_luma: Any,
        payoff_luma: Any,
        score_summary: dict[str, float],
    ) -> dict[str, Any]:
        hook_quality = self._score_hook(subtitle_cues, render_duration)
        payoff_quality = self._score_payoff(subtitle_cues, render_duration, payoff_luma)
        publishability_signal = self._score_publishability(
            hook_quality,
            payoff_quality,
            score_summary.get("edit_quality", 0.0),
            score_summary.get("asset_quality", 0.0),
        )
        return {
            "hook_quality": hook_quality,
            "payoff_quality": payoff_quality,
            "publishability_signal": publishability_signal,
            "publishable": (
                score_summary.get("overall_score", 0.0) >= 0.74
                and hook_quality >= 0.68
                and payoff_quality >= 0.6
                and publishability_signal >= 0.68
            ),
            "setup_luma_ok": not isinstance(setup_luma, (int, float)) or setup_luma >= 35,
        }

    def _collect_soft_failures(
        self,
        *,
        soft_failures: list[str],
        product_vetoes: list[str],
        score_summary: dict[str, float],
        product_signals: dict[str, Any],
    ) -> None:
        hook_quality = float(product_signals.get("hook_quality") or 0.0)
        payoff_quality = float(product_signals.get("payoff_quality") or 0.0)
        publishability_signal = float(product_signals.get("publishability_signal") or 0.0)
        overall_score = float(score_summary.get("overall_score") or 0.0)

        if hook_quality < 0.5:
            product_vetoes.append("QC_HOOK_QUALITY_FAIL")
        elif hook_quality < 0.68:
            soft_failures.append("QC_HOOK_QUALITY_BORDERLINE")

        if payoff_quality < 0.45:
            product_vetoes.append("QC_PAYOFF_QUALITY_FAIL")
        elif payoff_quality < 0.6:
            soft_failures.append("QC_PAYOFF_QUALITY_BORDERLINE")

        if publishability_signal < 0.5:
            product_vetoes.append("QC_PUBLISHABILITY_FAIL")
        elif publishability_signal < 0.68 or not bool(product_signals.get("publishable")):
            soft_failures.append("QC_PUBLISHABILITY_HOLD")

        if overall_score < 0.5:
            product_vetoes.append("QC_OVERALL_SCORE_FAIL")
        elif overall_score < 0.74:
            soft_failures.append("QC_OVERALL_SCORE_BORDERLINE")

    def _make_decision(
        self,
        *,
        checked_at: str,
        hard_failures: list[str],
        soft_failures: list[str],
        product_vetoes: list[str],
        score_summary: dict[str, float],
        product_signals: dict[str, Any],
        qc_input_governance: dict[str, Any],
    ) -> VideoQcDecision:
        if hard_failures or product_vetoes:
            status = "REJECT"
        elif soft_failures:
            status = "HOLD"
        else:
            status = "APPROVE"
        publishable = status == "APPROVE" and bool(product_signals.get("publishable"))
        return VideoQcDecision(
            status=status,
            publishable=publishable,
            hard_failures=list(dict.fromkeys(hard_failures)),
            soft_failures=list(dict.fromkeys(soft_failures)),
            product_vetoes=list(dict.fromkeys(product_vetoes)),
            score_summary=score_summary,
            product_signals=product_signals,
            decision_trace={
                "decision_order": [
                    "hard_failure_check",
                    "score_summary",
                    "product_signals",
                    "publishability_gate",
                ],
                "hard_failure_count": len(set(hard_failures)),
                "soft_failure_count": len(set(soft_failures)),
                "product_veto_count": len(set(product_vetoes)),
                "qc_input_governance": qc_input_governance,
            },
            checked_at=checked_at,
        )

    def _score_hook(self, subtitle_cues: list[dict[str, Any]], render_duration: float) -> float:
        if not subtitle_cues:
            return 0.0
        cue = subtitle_cues[0]
        text = str(cue.get("text") or "").replace("\n", " ").strip()
        words = len(text.split())
        duration = max(0.0, float(cue.get("end") or 0.0) - float(cue.get("start") or 0.0))
        landed_early = float(cue.get("start") or 0.0) <= 0.15
        word_score = 1.0 if 3 <= words <= 9 else 0.7 if 2 <= words <= 12 else 0.35
        duration_score = 1.0 if 1.2 <= duration <= 3.6 else 0.7 if 0.9 <= duration <= 4.2 else 0.35
        return _clamp_score((word_score * 0.4) + (duration_score * 0.4) + (0.2 if landed_early else 0.0))

    def _score_payoff(self, subtitle_cues: list[dict[str, Any]], render_duration: float, payoff_luma: Any) -> float:
        if not subtitle_cues or render_duration <= 0:
            return 0.0
        cue = subtitle_cues[-1]
        text = str(cue.get("text") or "").replace("\n", " ").strip()
        words = len(text.split())
        duration = max(0.0, float(cue.get("end") or 0.0) - float(cue.get("start") or 0.0))
        lands_near_end = (render_duration - float(cue.get("end") or 0.0)) <= 0.35
        word_score = 1.0 if 3 <= words <= 10 else 0.7 if 2 <= words <= 12 else 0.35
        duration_score = 1.0 if 1.1 <= duration <= 4.2 else 0.7 if 0.9 <= duration <= 4.6 else 0.35
        luma_score = 0.8
        if isinstance(payoff_luma, (int, float)):
            luma_score = 1.0 if 55 <= payoff_luma <= 185 else 0.7 if payoff_luma >= 45 else 0.0
        return _clamp_score((word_score * 0.35) + (duration_score * 0.35) + (0.15 if lands_near_end else 0.0) + (luma_score * 0.15))

    def _score_publishability(self, hook_quality: float, payoff_quality: float, edit_quality: float, asset_quality: float) -> float:
        return _clamp_score((hook_quality * 0.35) + (payoff_quality * 0.35) + (edit_quality * 0.15) + (asset_quality * 0.15))

    def _probe_video(self, video_path: Path) -> dict[str, object]:
        ffprobe = shutil.which("ffprobe")
        if not ffprobe:
            return {"width": None, "height": None, "has_audio": True, "probe_mode": "unavailable"}

        cmd = [
            ffprobe,
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_streams",
            str(video_path),
        ]
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        payload = json.loads(result.stdout or "{}")
        streams = payload.get("streams", [])
        video_stream = next((stream for stream in streams if stream.get("codec_type") == "video"), {})
        audio_stream = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
        return {
            "width": video_stream.get("width"),
            "height": video_stream.get("height"),
            "has_audio": audio_stream is not None,
            "probe_mode": "ffprobe",
        }

    def _infer_dimensions_from_metadata(self, metadata: dict[str, object]) -> dict[str, int]:
        aspect_ratio = str(metadata.get("aspect_ratio") or "")
        if aspect_ratio == "16:9":
            return {"width": 1280, "height": 720}
        return {"width": 1080, "height": 1920}
