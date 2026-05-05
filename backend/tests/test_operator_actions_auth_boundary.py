from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.v1.endpoints import operator_actions
from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def cleanup_metrics():
    yield


class _ActionResult:
    def __init__(self, *, action_type: str, operator_id: str):
        self.action_type = action_type
        self.operator_id = operator_id

    def to_dict(self):
        return {
            "action_type": self.action_type,
            "status": "WRITTEN",
            "reason_code": "TEST_ACTION",
            "target_id": "test-target",
            "details": {"operator_id": self.operator_id},
        }


class _FakeOperatorActionService:
    def __init__(self):
        self.calls = []

    def pause_rollout(self, *, operator_id: str, reason: str):
        self.calls.append({"action": "pause_rollout", "operator_id": operator_id, "reason": reason})
        return _ActionResult(action_type="pause-rollout", operator_id=operator_id)


@pytest.mark.anyio
async def test_operator_action_requires_control_plane_auth(monkeypatch):
    monkeypatch.setenv("CORTAI_CONTROL_PLANE_TOKEN", "test-control-plane-token")
    fake_service = _FakeOperatorActionService()
    monkeypatch.setattr(operator_actions, "_service", lambda: fake_service)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/ops/actions/pause-rollout",
            json={"operator_id": "attacker", "reason": "try unauthenticated control"},
        )

    assert response.status_code == 401
    assert fake_service.calls == []


@pytest.mark.anyio
async def test_operator_action_uses_verified_identity_not_payload_operator_id(monkeypatch):
    monkeypatch.setenv("CORTAI_CONTROL_PLANE_TOKEN", "test-control-plane-token")
    fake_service = _FakeOperatorActionService()
    monkeypatch.setattr(operator_actions, "_service", lambda: fake_service)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/ops/actions/pause-rollout",
            headers={"Authorization": "Bearer test-control-plane-token"},
            json={"operator_id": "attacker-controlled", "reason": "authorized control"},
        )

    assert response.status_code == 200
    assert fake_service.calls == [
        {
            "action": "pause_rollout",
            "operator_id": "control-plane-admin",
            "reason": "authorized control",
        }
    ]
    assert response.json()["details"]["operator_id"] == "control-plane-admin"
