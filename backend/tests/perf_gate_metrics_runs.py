import asyncio
import time
from datetime import datetime, timedelta

from httpx import ASGITransport, AsyncClient

from app.main import app

# Warmup reduz efeito de cold-start antes de medir o gate.
WARMUPS = 5
N = 50
P95_MAX_MS = 300
ERROR_RATE_MAX = 0.01


async def main() -> None:
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=7)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        for _ in range(WARMUPS):
            await client.get(
                "/api/v1/metrics/runs",
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "limit": 50,
                    "offset": 0,
                },
            )

        durations: list[float] = []
        errors = 0
        for _ in range(N):
            t0 = time.perf_counter()
            response = await client.get(
                "/api/v1/metrics/runs",
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "limit": 50,
                    "offset": 0,
                },
            )
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
