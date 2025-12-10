import os
from celery import Celery

# 1. Pegamos o endereço do Redis das variáveis de ambiente
# Se não houver variável, usa localhost como fallback (segurança para dev)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# 2. Criamos a instância do Celery
# 'cortai_worker' é o nome interno da aplicação
celery_app = Celery(
    "cortai_worker",
    broker=REDIS_URL,   # Onde as tarefas são enfileiradas (Redis)
    backend=REDIS_URL   # Onde os resultados são salvos (Redis)
)

# 3. Configurações de Robustez (Padrão Produção)
celery_app.conf.update(
    # Garante que só aceitamos JSON (segurança contra injeção de código pickle)
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Fuso horário correto
    timezone="UTC",
    enable_utc=True,
    
    # Se o worker morrer no meio de uma tarefa, re-enfileira a tarefa (ACK tardio)
    task_acks_late=True,
)