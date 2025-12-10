from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    return {
        "status": "ok",
        "services": {
            "api": "running",
        }
    }