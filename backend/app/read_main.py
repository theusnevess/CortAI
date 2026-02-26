import os
from time import perf_counter_ns

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import metrics, observability, status, internal_observability_ui
from app.version import get_app_version

# App dedicado ao read-path para isolar throughput de leitura.
app = FastAPI(
    title="CortAI Read API",
    description="Read-path dedicado (metrics + observability report + status)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

APP_VERSION = get_app_version()
GIT_TAG = os.getenv("GIT_TAG")
GIT_COMMIT = os.getenv("GIT_COMMIT")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def capture_asgi_entry_time(request: Request, call_next):
    """
    Mantem a mesma instrumentacao de fila ASGI usada na API principal.
    """
    request.state.asgi_entry_ns = perf_counter_ns()
    return await call_next(request)


app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["metrics"])
app.include_router(observability.router, prefix="/api/v1/observability", tags=["observability"])
app.include_router(status.router, prefix="/api/v1", tags=["status"])
app.include_router(internal_observability_ui.router)


@app.get("/")
def read_root():
    """
    Endpoint raiz do read-api.
    """
    return {
        "system": "CortAI Read API",
        "status": "online",
        "api_version": APP_VERSION,
    }


@app.get("/health")
def health_check():
    """
    Healthcheck do processo dedicado de leitura.
    """
    build_payload = {}
    if GIT_TAG:
        build_payload["git_tag"] = GIT_TAG
    if GIT_COMMIT:
        build_payload["git_commit"] = GIT_COMMIT

    payload = {
        "status": "ok",
        "api_version": APP_VERSION,
        "ces_default_version": metrics.CES_DEFAULT_VERSION,
        "services": {"read_api": "running"},
    }
    if build_payload:
        payload["build"] = build_payload
    return payload

