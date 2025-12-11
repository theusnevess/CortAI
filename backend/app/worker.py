import os # Acessa as variáveis de ambiente do SO
from celery import Celery # Cria um worker capaz de processar tarefas assíncronas

# Pega o endereço do Redis das variáveis de ambiente
# Se não houver variável, usa localhost como fallback do
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Cria a instância do Celery
celery_app = Celery(
    "cortai_worker",    # 'cortai_worker' é o nome interno da aplicação
    broker=REDIS_URL,   # Onde as tarefas são enfileiradas (Redis)
    backend=REDIS_URL   # Onde os resultados são salvos (Redis)
)

# Configurações de robustez e segurança
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
