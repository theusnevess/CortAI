import asyncio # Para suportar migrações assíncronas
from logging.config import fileConfig # Configuração de logging
import os # Para manipulação de variáveis de ambiente e caminhos
import sys # Para manipulação do Python Path
from sqlalchemy import pool # Pool de conexões
from sqlalchemy.ext.asyncio import async_engine_from_config # Motor de banco de dados assíncrono
from alembic import context # Contexto do Alembic

# --- CONFIGURAÇÃO CORTAI ---
# Adiciona o diretório 'app' ao Python Path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Importa a Base e os Modelos (para o Alembic "ver" as tabelas)
from app.db.base import Base
from app.db.models import User, Video, VideoSegment, Clip
# --------------------------------------------------------------------------------------------------------------------------------

config = context.config # Configuração do Alembic

# Configura o logging a partir do arquivo de configuração
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Aponta os metadados para a nossa Base
target_metadata = Base.metadata

# --------------------------------------------------------------------------------------------------------------------------------
def get_url():
    """
    Pega a URL do banco das variáveis de ambiente.
    """

    # O container Docker já tem essa variável, mas deixamos um fallback seguro
    return os.getenv("DATABASE_URL", "postgresql://cortai_admin:cortai_secret_pass_123@db:5432/cortai_db").replace("postgresql://", "postgresql+asyncpg://")

# --------------------------------------------------------------------------------------------------------------------------------

def run_migrations_offline() -> None:
    """
    Executa migrações no modo offline.
    """
    url = get_url()
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"}
    )
    with context.begin_transaction():
        context.run_migrations()

# --------------------------------------------------------------------------------------------------------------------------------

def do_run_migrations(connection):
    """
    Excuta as migrações com a conexão fornecida.
    """
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

# --------------------------------------------------------------------------------------------------------------------------------

async def run_migrations_online() -> None:
    """
    Executa migrações no modo online.
    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = async_engine_from_config(
        configuration, prefix="sqlalchemy.", poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

# --------------------------------------------------------------------------------------------------------------------------------

# Executa as migrações no modo apropriado
if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
