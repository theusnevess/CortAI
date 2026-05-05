from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.read_main import app as read_app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def cleanup_metrics():
    yield


@pytest.mark.anyio
async def test_read_api_does_not_expose_operator_action_mutations():
    async with AsyncClient(transport=ASGITransport(app=read_app), base_url="http://readtest") as client:
        response = await client.post(
            "/api/v1/ops/actions/pause-rollout",
            headers={"Authorization": "Bearer any-token"},
            json={"operator_id": "attacker", "reason": "read api must not mutate"},
        )

    assert response.status_code == 404
