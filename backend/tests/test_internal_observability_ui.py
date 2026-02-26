import pytest

from app.api.v1.endpoints import internal_observability_ui as internal_ui


def _internal_headers() -> dict[str, str]:
    return {"X-Internal-Status": "1"}


def _fake_panel_payload() -> dict:
    return {
        "as_of": "2026-02-26T00:00:00Z",
        "panel_version": "v1",
        "overall": {"score": "PASS", "decision": "healthy", "reasons": []},
        "trust": {
            "state": "green",
            "decision": "healthy",
            "message": "All systems healthy",
            "derived_from": ["c1_health"],
        },
        "recommendation": {
            "action": "none",
            "priority": "low",
            "message": "Nenhuma acao necessaria.",
            "derived_from": ["trust"],
        },
        "c1_health": {"score": "PASS", "version": "v1.1", "meta": {"cached": True}, "rows": []},
        "read_path": {
            "overview_snapshot_status": "fresh",
            "overview_freshness_seconds": 1,
            "runs_snapshot_status": "fresh",
            "runs_freshness_seconds": 1,
            "runs_key_count": 1,
            "jobs_queued_count": 0,
        },
        "guardrails": {
            "window_minutes": 15,
            "events": {"accepted_202": 0, "rate_limited_429": 0, "snapshot_missing_503": 0},
            "last_events": [],
        },
    }


@pytest.mark.anyio
async def test_internal_observability_ui_gate_off_returns_404(client, monkeypatch):
    monkeypatch.delenv("EXPOSE_C1_HEALTH_STATUS", raising=False)
    response = await client.get("/internal/observability", headers=_internal_headers())
    assert response.status_code == 404


@pytest.mark.anyio
async def test_internal_observability_ui_gate_on_without_header_returns_404(client, monkeypatch):
    monkeypatch.setenv("EXPOSE_C1_HEALTH_STATUS", "1")
    response = await client.get("/internal/observability")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_internal_observability_ui_gate_on_returns_html_200(client, monkeypatch):
    monkeypatch.setenv("EXPOSE_C1_HEALTH_STATUS", "1")

    async def _fake_builder(**kwargs):
        return _fake_panel_payload()

    monkeypatch.setattr(internal_ui, "_build_observability_overview_payload", _fake_builder)

    response = await client.get("/internal/observability", headers=_internal_headers())
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "").lower()

    body = response.text
    for anchor in ("Operational Insights", "TRUST:", "Recommendation", "C1 Health", "Read Path", "Guardrails"):
        assert anchor in body


@pytest.mark.anyio
async def test_internal_observability_ui_no_store_header(client, monkeypatch):
    monkeypatch.setenv("EXPOSE_C1_HEALTH_STATUS", "1")

    async def _fake_builder(**kwargs):
        return {
            "panel_version": "v1",
            "overall": {},
            "c1_health": {},
            "read_path": {},
            "guardrails": {},
        }

    monkeypatch.setattr(internal_ui, "_build_observability_overview_payload", _fake_builder)

    response = await client.get("/internal/observability", headers=_internal_headers())
    assert response.status_code == 200
    assert response.headers.get("cache-control") == "no-store"


@pytest.mark.anyio
async def test_internal_observability_ui_renders_with_minimal_payload(client, monkeypatch):
    monkeypatch.setenv("EXPOSE_C1_HEALTH_STATUS", "1")

    async def _minimal_builder(**kwargs):
        # Intencionalmente incompleto para validar defaults do template.
        return {"panel_version": "v1"}

    monkeypatch.setattr(internal_ui, "_build_observability_overview_payload", _minimal_builder)

    response = await client.get("/internal/observability", headers=_internal_headers())
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "").lower()
    assert "Operational Insights" in response.text
    assert "TRUST:" in response.text

