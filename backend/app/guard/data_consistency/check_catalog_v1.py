from __future__ import annotations

from typing import Final

CHECK_CATALOG_V1: Final[dict[str, dict[str, str]]] = {
    "VCG_001": {
        "description": "video_metrics deve referenciar video_id existente em publish_records",
        "severity": "ERROR",
        "action": "BLOCK",
        "reason_code": "VCG_001_VIDEO_WITHOUT_PUBLISH_RECORD",
    },
    "VCG_002": {
        "description": "publish_record.job_id deve existir no repositorio de job_specs",
        "severity": "WARN",
        "action": "SOFT",
        "reason_code": "VCG_002_JOB_SPEC_LINK_CHECK",
    },
    "VCG_003": {
        "description": "videos_considered deve ser igual ao total de publishes na janela",
        "severity": "ERROR",
        "action": "BLOCK",
        "reason_code": "VCG_003_WINDOW_CONSIDERED_MISMATCH",
    },
    "VCG_004": {
        "description": "videos_with_metrics + videos_missing_metrics deve fechar com videos_considered",
        "severity": "ERROR",
        "action": "BLOCK",
        "reason_code": "VCG_004_METRICS_ACCOUNTING_MISMATCH",
    },
    "VCG_005": {
        "description": "scorecard e attribution devem usar o mesmo window_id",
        "severity": "ERROR",
        "action": "BLOCK",
        "reason_code": "VCG_005_CROSS_ARTIFACT_WINDOW_MISMATCH",
    },
}

