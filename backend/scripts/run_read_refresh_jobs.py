#!/usr/bin/env python
"""
Executa jobs enfileirados de refresh dos read models de metrics.
"""

from __future__ import annotations

import argparse
import asyncio

from app.api.v1.endpoints.metrics import process_read_refresh_jobs_once
from app.db.session import AsyncSessionLocal


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Processa fila de refresh dos read models")
    parser.add_argument("--limit", type=int, default=100, help="Maximo de jobs por execucao")
    return parser.parse_args()


async def _run(limit: int) -> None:
    async with AsyncSessionLocal() as db:
        result = await process_read_refresh_jobs_once(db=db, limit=limit)
        print(
            f"processed={result['processed']} succeeded={result['succeeded']} failed={result['failed']}"
        )


def main() -> None:
    args = _parse_args()
    asyncio.run(_run(limit=max(1, int(args.limit))))


if __name__ == "__main__":
    main()

