from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker # Ferramentas assíncronas do SQLALchemy
from app.db.base import Base # Importa a base dos modelos
from app.config.runtime import require_async_database_url

_engine = None
_AsyncSessionLocal = None


class _LazyAsyncEngine:
    def _get(self):
        return get_async_engine()

    def __getattr__(self, name):
        return getattr(self._get(), name)


class _LazyAsyncSessionmaker:
    def _get(self):
        return get_async_sessionmaker()

    def __call__(self, *args, **kwargs):
        return self._get()(*args, **kwargs)


def get_async_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(require_async_database_url(), echo=False)
    return _engine


def get_async_sessionmaker():
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        _AsyncSessionLocal = async_sessionmaker(
            bind=get_async_engine(),
            expire_on_commit=False,
            autoflush=False,
        )
    return _AsyncSessionLocal


engine = _LazyAsyncEngine()
AsyncSessionLocal = _LazyAsyncSessionmaker()

# Dependency Injection (Para usar no FastAPI)
# Essa função será usada nas rotas: "async def create_user(db: AsyncSession = Depends(get_db))"
async def get_db():
    async with get_async_sessionmaker()() as session:
        try:
            yield session
        finally:
            await session.close()
