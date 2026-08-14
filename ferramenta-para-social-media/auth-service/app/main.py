from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import router

app = FastAPI(
    title="Auth Service",
    description="Serviço de autenticação — login e validação de token",
    version="1.0.0",
)

# CORS: controla quais sites/domínios podem chamar essa API pelo navegador.
# Por enquanto liberado geral; quando o frontend tiver domínio definido,
# vamos restringir isso à(s) sua(s) URL(s) real(is).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra as rotas de app/routes.py (login, /me) na aplicação
app.include_router(router)


@app.get("/health")
def health_check():
    """Rota simples pra confirmar que o serviço está de pé.
    Útil pro Docker/Portainer monitorar a saúde do container."""
    return {"status": "ok", "service": "auth-service"}