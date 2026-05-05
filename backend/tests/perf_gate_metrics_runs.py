import asyncio
import time
from datetime import datetime, timedelta

from httpx import ASGITransport, AsyncClient

from app.api.v1.endpoints.metrics import process_read_refresh_jobs_once
from app.db.session import AsyncSessionLocal
from app.main import app

# Warmup reduz efeito de cold-start antes de medir o gate.
WARMUPS = 5
N = 50
P95_MAX_MS = 300
ERROR_RATE_MAX = 0.01


def _query_params(start_date, end_date) -> dict[str, str | int]:
    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "limit": 50,
        "offset": 0,
    }


async def _prepare_snapshot(client: AsyncClient, params: dict[str, str | int]) -> None:
    accepted = await client.get(
        "/api/v1/metrics/runs",
        params={**params, "force_live": "true"},
    )
    assert accepted.status_code == 202, f"snapshot precondition enqueue failed: {accepted.status_code}"

    async with AsyncSessionLocal() as db:
        await process_read_refresh_jobs_once(db=db, limit=20)

    ready = await client.get("/api/v1/metrics/runs", params=params)
    assert ready.status_code == 200, f"snapshot precondition missing after refresh: {ready.status_code}"


async def main() -> None:
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=7)
    params = _query_params(start_date, end_date)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        await _prepare_snapshot(client, params)

        for _ in range(WARMUPS):
            await client.get("/api/v1/metrics/runs", params=params)

        durations: list[float] = []
        errors = 0
        for _ in range(N):
            t0 = time.perf_counter()
            response = await client.get("/api/v1/metrics/runs", params=params)
            durations.append((time.perf_counter() - t0) * 1000.0)
            if response.status_code >= 400:
                errors += 1

    ordered = sorted(durations)
    p95 = ordered[int(0.95 * (len(ordered) - 1))]
    error_rate = errors / float(N)

    print(f"PERF_GATE p95_ms={p95:.2f} error_rate={error_rate:.4f}")
    assert p95 <= P95_MAX_MS, f"p95 {p95:.2f}ms > {P95_MAX_MS}ms"
    assert error_rate <= ERROR_RATE_MAX, f"error_rate {error_rate:.4f} > {ERROR_RATE_MAX:.4f}"


if __name__ == "__main__":
    asyncio.run(main())
