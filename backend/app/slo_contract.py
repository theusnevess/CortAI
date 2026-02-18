# Contrato unico de SLO por endpoint para evitar drift entre docs, agregacao e status.
SLO_ENDPOINT_THRESHOLDS = {
    "/api/v1/metrics/runs": {"p95_ms": 150, "p99_ms": 300, "error_rate": 0.01},
    "/api/v1/metrics/runs/{process_id}": {"p95_ms": 200, "p99_ms": 400, "error_rate": 0.01},
    "/api/v1/metrics/overview": {"p95_ms": 120, "p99_ms": 250, "error_rate": 0.01},
    "/api/v1/observability/report": {"p95_ms": 300, "p99_ms": 600, "error_rate": 0.01},
}

SLO_STATUS_WINDOW_DAYS_DEFAULT = 7
SLO_STATUS_WINDOW_DAYS_MAX = 30
