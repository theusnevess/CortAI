import os # Acessar as variáveis de ambiente do SO
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker # Ferramentas assíncronas do SQLALchemy
from app.db.base import Base # Importa a base dos modelos

# Pega a URL do .env. 
# Se não existir, usamos um padrão seguro para dev local
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://cortai_admin:cortai_secret_pass_123@db:5432/cortai_db")

# Ajuste Técnico: O driver padrão do SQLAlchemy é síncrono.
# Trocar para o driver assíncrono 'asyncpg'.
ASYNC_DB_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Cria o motor (Engine)
# echo=False desliga logs excessivos de SQL no terminal
engine = create_async_engine(ASYNC_DB_URL, echo=False)

# Cada vez que alguém chamar a API, cria uma 'session' nova para isolar os dados.
AsyncSessionLocal = async_sessionmaker(
    bind=engine, # Liga o motor criado acima
    expire_on_commit=False, # Boas práticas para modo assíncrono
    autoflush=False # Não envia mudanças automaticamente ao banco
)

# Dependency Injection (Para usar no FastAPI)
# Essa função será usada nas rotas: "async def create_user(db: AsyncSession = Depends(get_db))"
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()