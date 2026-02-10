import os # Acessa as variáveis de ambiente do SO
from celery import Celery
from celery.schedules import crontab # Cria um worker capaz de processar tarefas assíncronas

# Pega o endereço do Redis das variáveis de ambiente
# Se não houver variável, usa localhost como fallback do
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Cria a instância do Celery
celery_app = Celery(
    "cortai_worker",    # 'cortai_worker' é o nome interno da aplicação
    broker=REDIS_URL,   # Onde as tarefas são enfileiradas (Redis)
    backend=REDIS_URL,  # Onde os resultados são salvos (Redis)

    # Inclui explicitamente o módulo de tasks para garantir que o worker
    # registre tarefas definidas em `app.tasks.*` (ex: collector.process_video)
    include=[
        "app.tasks.collector_tasks",
    ]
)

# Autodiscover tasks também (compatibilidade extra)
celery_app.autodiscover_tasks(["app.tasks"], force=True)

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
    
    # Agendamento diario da telemetria (ontem UTC)
    beat_schedule={
        "cognitive-aggregate-daily-metrics": {
            "task": "cognitive.aggregate_daily_metrics",
            "schedule": crontab(hour=0, minute=10),
            "args": (None,),
        },
    },
)

def execute_action(decision_id: str, action_type: str, action_payload: dict):
    """
    Executa a ação decidida pelo ciclo cognitivo.
    """
    return {
        "decision_id": decision_id,
        "execution_status": "SUCCESS",
        "metrics": {}
    }



