import os
from time import perf_counter_ns

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import (
    videos,
    metrics,
    observability,
    status,
    events,
    ops_dashboard,
    operator_actions,
    strategy_observatory,
    internal_observability_ui,
    internal_maestro,
)
from app.cognitive_core import run_cognitive_cycle
from app.version import get_app_version
from app.ops.readiness import evaluate_readiness
from fastapi.responses import JSONResponse

# --- Inicialização da Aplicação ---
# Criando a instância principal do FastAPI.
# title/description/version: Esses dados aparecem automaticamente na documentação
# interativa (Swagger UI) que o FastAPI gera em /docs.
app = FastAPI(
    title="CortAI API",
    description="Engine de Automação de Conteúdo Multimodal (Big Tech Level)",
    version="1.0.0",
    docs_url="/docs",  # URL da documentação (Swagger)
    redoc_url="/redoc" # URL da documentação alternativa (ReDoc)
)

APP_VERSION = get_app_version()
GIT_TAG = os.getenv("GIT_TAG")
GIT_COMMIT = os.getenv("GIT_COMMIT")

# --- Configuração de CORS (Cross-Origin Resource Sharing) ---
# CRÍTICO: O CORS é uma medida de segurança dos navegadores.
# Como o Frontend roda na porta 3000 e o Backend na 8000, o navegador bloquearia a comunicação por padrão. O Middleware abaixo libera esse acesso.
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      
    allow_credentials=True,     
    allow_methods=["*"],        
    allow_headers=["*"],        
)


@app.middleware("http")
async def capture_asgi_entry_time(request: Request, call_next):
    """
    Captura timestamp de entrada ASGI para medir fila antes do handler.
    """
    request.state.asgi_entry_ns = perf_counter_ns()
    response = await call_next(request)
    return response

app.include_router(videos.router, prefix="/api/v1/videos", tags=["videos"])
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["metrics"])
app.include_router(observability.router, prefix="/api/v1/observability", tags=["observability"])
app.include_router(events.router, prefix="/api/v1/events", tags=["events"])
app.include_router(ops_dashboard.router, prefix="/api/v1/ops", tags=["ops"])
app.include_router(operator_actions.router, prefix="/api/v1/ops/actions", tags=["ops-actions"])
app.include_router(strategy_observatory.router, prefix="/api/v1/ops/strategy", tags=["ops-strategy"])
app.include_router(status.router, prefix="/api/v1", tags=["status"])
app.include_router(internal_observability_ui.router)
app.include_router(internal_maestro.router)

# --- Rotas (Endpoints) ---

@app.get("/")
def read_root():
    """
    Rota Raiz.
    Serve apenas como um 'Olá' para verificar se o servidor subiu.
    Retorna um JSON simples.
    """
    return {
        "system": "CortAI",
        "architecture": "Event-Driven / Microservices",
        "status": "online",
        "message": "Welcome to the Big Tech AI Engine"
    }

@app.get("/health")
def health_check():
    """
    Health Check (Checagem de Saúde).
    
    EXTREMAMENTE IMPORTANTE PARA INFRAESTRUTURA:
    O Kubernetes ou o Docker usam essa rota para saber se o container
    está vivo. Se essa rota não responder '200 OK', o orquestrador
    mata o container e sobe um novo[cite: 1028].
    """
    build_payload = {}
    if GIT_TAG:
        build_payload["git_tag"] = GIT_TAG
    if GIT_COMMIT:
        build_payload["git_commit"] = GIT_COMMIT

    response = {
        "status": "ok",
        "api_version": APP_VERSION,
        "ces_default_version": metrics.CES_DEFAULT_VERSION,
        "services": {
            "api": "running",
        },
    }
    if build_payload:
        response["build"] = build_payload
    return response


@app.get("/ready")
def readiness_check():
    """Readiness operacional para rollout e expansão."""
    status = evaluate_readiness()
    payload = status.to_dict()
    if status.ready:
        return payload
    return JSONResponse(status_code=503, content=payload)

# Ponto único de entrada da observação
def execute_action(decision_id: str, action_type: str, action_payload: dict):
    return {
        "decision_id": decision_id,
        "execution_status": "SUCCESS",
        "metrics": {}
    }


@app.post("/observe")
def observe(payload: dict):
    """
    Ponto de entrada para observações externas.
    Recebe uma observação via payload JSON e inicia um ciclo cognitivo.
    """
    run_cognitive_cycle(
        observation_payload=payload,
        executor_callback=execute_action
    )
    return {"status": "accepted"} # Retorna 202 Accepted para indicar que a observação foi recebida e está sendo processada
