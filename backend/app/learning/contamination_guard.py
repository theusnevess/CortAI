from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


LABELS = {"CLEAN", "CONTAMINATED", "WEAK_SIGNAL", "INSUFFICIENT", "NOISY"}


@dataclass(frozen=True)
class EvidenceClassification:
    label: str
    reasons: list[str] = field(default_factory=list)
    usable_for_policy: bool = False
    confidence_penalty: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ClusterContaminationReport:
    sample_size: int
    clean_count: int
    contaminated_count: int
    weak_signal_count: int
    insufficient_count: int
    noisy_count: int
    cleanliness_ratio: float
    dominant_label: str
    usable_for_patterning: bool
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DatasetContaminationSummary:
    sample_size: int
    clean_sample_size: int
    contamination_rate: float
    weak_signal_rate: float
    noise_rate: float
    insufficient_rate: float
    dominant_problem: str
    policy_safe: bool
    confidence_penalty: float
    cluster_report: ClusterContaminationReport
    classifications: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["cluster_report"] = self.cluster_report.to_dict()
        return payload


class LearningContaminationGuard:
    """Classifies evidence quality before Learning uses it for confidence/policy."""

    def classify_evidence_item(self, evidence_item: dict[str, Any]) -> EvidenceClassification:
        item = evidence_item if isinstance(evidence_item, dict) else {}
        status = str(item.get("status") or "").upper()
        score = self._score(item)
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        fallback_used = bool(
            item.get("fallback_used")
            or item.get("contaminated")
            or item.get("script_fallback")
            or item.get("asset_fallback")
            or item.get("voice_fallback")
            or metadata.get("fallback_used")
            or metadata.get("fallback")
        )
        missing_metadata = bool(item.get("missing_metadata")) or not metadata
        reasons: list[str] = []

        if fallback_used:
            return EvidenceClassification(
                label="CONTAMINATED",
                reasons=["fallback_or_degraded_runtime_path"],
                usable_for_policy=False,
                confidence_penalty=0.45,
            )

        if status not in {"APPROVE", "HOLD", "REJECT"} and score <= 0:
            return EvidenceClassification(
                label="INSUFFICIENT",
                reasons=["missing_status_and_score"],
                usable_for_policy=False,
                confidence_penalty=0.4,
            )

        if missing_metadata and score <= 0:
            return EvidenceClassification(
                label="INSUFFICIENT",
                reasons=["missing_metadata"],
                usable_for_policy=False,
                confidence_penalty=0.35,
            )

        if self._contradictory_status_score(status=status, score=score):
            return EvidenceClassification(
                label="NOISY",
                reasons=["status_score_contradiction"],
                usable_for_policy=False,
                confidence_penalty=0.42,
            )

        if score <= 0 or 0.55 < score < 0.7:
            reasons.append("low_qc_informativeness")
            if missing_metadata:
                reasons.append("metadata_limited")
            return EvidenceClassification(
                label="WEAK_SIGNAL",
                reasons=reasons,
                usable_for_policy=True,
                confidence_penalty=0.2,
            )

        if missing_metadata:
            return EvidenceClassification(
                label="WEAK_SIGNAL",
                reasons=["metadata_limited"],
                usable_for_policy=True,
                confidence_penalty=0.15,
            )

        return EvidenceClassification(
            label="CLEAN",
            reasons=["sufficient_metadata_and_signal"],
            usable_for_policy=True,
            confidence_penalty=0.0,
        )

    def analyze_cluster(self, evidence_items: list[dict[str, Any]]) -> ClusterContaminationReport:
        classifications = [self.classify_evidence_item(item) for item in evidence_items]
        sample_size = len(classifications)
        counts = self._label_counts(classifications)
        cluster_noisy = self._cluster_is_noisy(evidence_items)
        noisy_count = counts["NOISY"]
        reasons: list[str] = []
        if cluster_noisy:
            noisy_count = max(noisy_count, sample_size - counts["CONTAMINATED"] - counts["INSUFFICIENT"])
            reasons.append("mixed_outcomes_without_score_separation")

        clean_count = counts["CLEAN"]
        cleanliness_ratio = self._rate(clean_count, sample_size)
        dominant_label = self._dominant_label(
            {
                "CLEAN": clean_count,
                "CONTAMINATED": counts["CONTAMINATED"],
                "WEAK_SIGNAL": counts["WEAK_SIGNAL"],
                "INSUFFICIENT": counts["INSUFFICIENT"],
                "NOISY": noisy_count,
            }
        )
        usable_for_patterning = (
            sample_size >= 5
            and clean_count >= 5
            and cleanliness_ratio >= 0.6
            and self._rate(noisy_count, sample_size) <= 0.35
            and dominant_label not in {"NOISY", "INSUFFICIENT", "CONTAMINATED"}
        )
        return ClusterContaminationReport(
            sample_size=sample_size,
            clean_count=clean_count,
            contaminated_count=counts["CONTAMINATED"],
            weak_signal_count=counts["WEAK_SIGNAL"],
            insufficient_count=counts["INSUFFICIENT"],
            noisy_count=noisy_count,
            cleanliness_ratio=cleanliness_ratio,
            dominant_label=dominant_label,
            usable_for_patterning=usable_for_patterning,
            reasons=reasons,
        )

    def summarize_dataset(self, evidence_items: list[dict[str, Any]]) -> DatasetContaminationSummary:
        classifications = [self.classify_evidence_item(item) for item in evidence_items]
        report = self.analyze_cluster(evidence_items)
        sample_size = report.sample_size
        contamination_rate = self._rate(report.contaminated_count, sample_size)
        weak_signal_rate = self._rate(report.weak_signal_count, sample_size)
        noise_rate = self._rate(report.noisy_count, sample_size)
        insufficient_rate = self._rate(report.insufficient_count, sample_size)
        dominant_problem = self._dominant_problem(
            contamination_rate=contamination_rate,
            weak_signal_rate=weak_signal_rate,
            noise_rate=noise_rate,
            insufficient_rate=insufficient_rate,
        )
        policy_safe = (
            sample_size >= 5
            and report.clean_count >= 5
            and contamination_rate <= 0.4
            and noise_rate <= 0.35
            and insufficient_rate <= 0.45
            and report.dominant_label not in {"CONTAMINATED", "NOISY", "INSUFFICIENT"}
        )
        return DatasetContaminationSummary(
            sample_size=sample_size,
            clean_sample_size=report.clean_count,
            contamination_rate=contamination_rate,
            weak_signal_rate=weak_signal_rate,
            noise_rate=noise_rate,
            insufficient_rate=insufficient_rate,
            dominant_problem=dominant_problem,
            policy_safe=policy_safe,
            confidence_penalty=self._dataset_penalty(
                contamination_rate=contamination_rate,
                weak_signal_rate=weak_signal_rate,
                noise_rate=noise_rate,
                insufficient_rate=insufficient_rate,
                policy_safe=policy_safe,
            ),
            cluster_report=report,
            classifications=[item.to_dict() for item in classifications],
        )

    def _cluster_is_noisy(self, evidence_items: list[dict[str, Any]]) -> bool:
        rows = [item for item in evidence_items if isinstance(item, dict) and not bool(item.get("contaminated") or item.get("fallback_used"))]
        if len(rows) < 5:
            return False
        statuses = {str(row.get("status") or "").upper() for row in rows}
        if len(statuses.intersection({"APPROVE", "HOLD", "REJECT"})) < 2:
            return False
        approved = [self._score(row) for row in rows if str(row.get("status") or "").upper() == "APPROVE" and self._score(row) > 0]
        negative = [self._score(row) for row in rows if str(row.get("status") or "").upper() in {"HOLD", "REJECT"} and self._score(row) > 0]
        if not approved or not negative:
            return False
        separation = abs((sum(approved) / len(approved)) - (sum(negative) / len(negative)))
        return separation < 0.12

    def _score(self, item: dict[str, Any]) -> float:
        for key in ("overall_score", "product_quality", "product_score", "raw_value", "completion_rate"):
            value = item.get(key)
            if isinstance(value, (int, float)):
                return self._clamp(value)
        return 0.0

    def _contradictory_status_score(self, *, status: str, score: float) -> bool:
        if status == "APPROVE" and 0 < score < 0.55:
            return True
        if status in {"HOLD", "REJECT"} and score >= 0.82:
            return True
        return False

    def _label_counts(self, classifications: list[EvidenceClassification]) -> dict[str, int]:
        return {label: sum(1 for item in classifications if item.label == label) for label in LABELS}

    def _dominant_label(self, counts: dict[str, int]) -> str:
        if not counts or sum(counts.values()) <= 0:
            return "INSUFFICIENT"
        return max(sorted(counts), key=lambda label: counts[label])

    def _dominant_problem(
        self,
        *,
        contamination_rate: float,
        weak_signal_rate: float,
        noise_rate: float,
        insufficient_rate: float,
    ) -> str:
        rates = {
            "contamination": contamination_rate,
            "weak_signal": weak_signal_rate,
            "noise": noise_rate,
            "insufficient": insufficient_rate,
        }
        label, value = max(rates.items(), key=lambda item: (item[1], item[0]))
        return label if value > 0 else "none"

    def _dataset_penalty(
        self,
        *,
        contamination_rate: float,
        weak_signal_rate: float,
        noise_rate: float,
        insufficient_rate: float,
        policy_safe: bool,
    ) -> float:
        penalty = (
            contamination_rate * 0.35
            + weak_signal_rate * 0.18
            + noise_rate * 0.4
            + insufficient_rate * 0.28
        )
        if not policy_safe:
            penalty += 0.08
        return round(min(0.55, penalty), 4)

    def _rate(self, count: int, total: int) -> float:
        if total <= 0:
            return 0.0
        return round(count / total, 4)

    def _clamp(self, value: float) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            numeric = 0.0
        return max(0.0, min(1.0, round(numeric, 4)))
