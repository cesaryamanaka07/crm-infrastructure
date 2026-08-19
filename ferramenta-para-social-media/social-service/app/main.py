import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.clientes_routes import router as clientes_router
from app.oauth_routes import router as oauth_router
from app.routes import router
from app.webhook_routes import router as webhook_router
from app.publicacoes_routes import router as publicacoes_router
from app.token_refresh import executar_renovacao_automatica
from app.agendamento import executar_agendamento


@asynccontextmanager
async def lifespan(app):
    renovacao = asyncio.create_task(executar_renovacao_automatica())
    agendamento = asyncio.create_task(executar_agendamento())
    yield
    renovacao.cancel()
    agendamento.cancel()


app = FastAPI(title="Social Service", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins_list, allow_credentials=True,
                   allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], allow_headers=["Authorization", "Content-Type"])
app.include_router(router)
app.include_router(oauth_router)
app.include_router(clientes_router)
app.include_router(webhook_router)
app.include_router(publicacoes_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "social-service"}
