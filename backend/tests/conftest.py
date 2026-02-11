import os
import sys
import uuid
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, delete, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db.models import CognitiveMetricsDaily, ObservationRecord
from app.db.session import get_db
from app.main import app

# Fixtures de teste para API e banco com isolamento por transacao.

# Configura backend de teste para anyio.
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

# Helpers para configurar conexao com banco de teste e criar sessoes isoladas por teste.
def _get_database_url() -> str:
    db_url = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("Set TEST_DATABASE_URL or DATABASE_URL for integration tests")
    return db_url

# Converte DATABASE_URL para formato asyncpg se necessario.
def _as_async_database_url(db_url: str) -> str:
    if db_url.startswith("postgresql+asyncpg://"):
        return db_url
    return db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Fixtures para testes de API e banco.
@pytest.fixture(scope="session")
def database_url() -> str:
    return _get_database_url()

# Fixture para criar engine async para testes que precisam de acesso direto.
@pytest.fixture(scope="session")
def async_database_url(database_url: str) -> str:
    return _as_async_database_url(database_url)

# Fixture para criar engine async e garantir dispose ao final dos testes.
@pytest.fixture(scope="session")
async def async_engine(async_database_url: str):
    engine = create_async_engine(async_database_url, future=True)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
async def db_session(async_engine) -> AsyncSession:
    """
    Cria sessao assincrona com SAVEPOINT para isolamento por teste.
    """
    async with async_engine.connect() as connection:
        transaction = await connection.begin()
        session_factory = async_sessionmaker(
            bind=connection,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        async with session_factory() as session:
            await session.begin_nested()

            # Reabre SAVEPOINT apos commits no codigo sob teste.
            @event.listens_for(session.sync_session, "after_transaction_end")
            def restart_savepoint(sess, trans):
                if trans.nested and trans.parent and not trans.parent.nested:
                    sess.begin_nested()

            try:
                yield session
            finally:
                await session.close()
                await transaction.rollback()


@pytest.fixture
async def client(db_session: AsyncSession):
    """
    Cliente HTTP assincrono para testes com override de get_db.
    """
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def seed_observation(db_session: AsyncSession):
    """
    Helper para inserir observacoes no banco durante testes.
    """
    async def _seed(
        *,
        observation_id: str | None = None,
        timestamp: datetime,
        process_id: str,
        source_outcome_id: str,
        facts: dict,
    ) -> ObservationRecord:
        record = ObservationRecord(
            observation_id=observation_id or str(uuid.uuid4()),
            timestamp=timestamp,
            process_id=process_id,
            source_outcome_id=source_outcome_id,
            facts=facts,
        )
        db_session.add(record)
        await db_session.flush()
        return record

    return _seed


@pytest.fixture
async def seed_daily_metric(db_session: AsyncSession):
    """
    Helper para inserir metricas diarias no banco durante testes.
    """
    async def _seed(
        *,
        metric_date: date,
        total_runs: int,
        completed_runs: int,
        failed_runs: int,
        blocked_runs: int,
        avg_actions_executed: float | str | Decimal | None,
        last_action_type_distribution: dict,
        truncated_runs: int = 0,
        truncated_ratio: float | str | Decimal | None = Decimal("0.00"),
        latency_by_action: dict | None = None,
    ) -> CognitiveMetricsDaily:
        await db_session.execute(
            delete(CognitiveMetricsDaily).where(CognitiveMetricsDaily.metric_date == metric_date)
        )
        metric = CognitiveMetricsDaily(
            id=uuid.uuid4(),
            metric_date=metric_date,
            total_runs=total_runs,
            completed_runs=completed_runs,
            failed_runs=failed_runs,
            blocked_runs=blocked_runs,
            truncated_runs=truncated_runs,
            truncated_ratio=(
                Decimal(str(truncated_ratio)) if truncated_ratio is not None else None
            ),
            avg_actions_executed=(
                Decimal(str(avg_actions_executed)) if avg_actions_executed is not None else None
            ),
            last_action_type_distribution=last_action_type_distribution,
            latency_by_action=latency_by_action or {},
        )
        db_session.add(metric)
        await db_session.flush()
        return metric

    return _seed


@pytest.fixture
def sync_session_factory(database_url: str):
    """
    Fabrica de sessoes sincronas para operacoes de cleanup.
    """
    engine = create_engine(database_url)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    try:
        yield factory
    finally:
        engine.dispose()


@pytest.fixture(autouse=True)
def cleanup_metrics(sync_session_factory):
    """
    Limpa dados de metricas/alertas antes e depois de cada teste.
    """
    target_dates = [date(2026, 2, 8), date(2026, 2, 9), date(2026, 2, 10)]
    session = sync_session_factory()
    try:
        session.execute(
            delete(CognitiveMetricsDaily).where(CognitiveMetricsDaily.metric_date.in_(target_dates))
        )
        session.execute(
            delete(ObservationRecord).where(
                ObservationRecord.facts["event_type"].astext == "cognitive_metrics_alert"
            )
        )
        session.execute(
            delete(ObservationRecord).where(ObservationRecord.process_id.like("P_METRICS_DAILY_%"))
        )
        session.execute(
            delete(ObservationRecord).where(ObservationRecord.process_id.like("P_TEST_GUARDRAIL_%"))
        )
        session.commit()
        yield
    finally:
        session.close()
