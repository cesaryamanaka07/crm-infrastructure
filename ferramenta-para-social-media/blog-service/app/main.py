import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.config import settings
from app.database import Base, engine
from app.routes import router
from app.scheduler import executar_agenda


@asynccontextmanager
async def lifespan(app):
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS blog"))
        conn.execute(text("ALTER TABLE IF EXISTS blog.integracoes ADD COLUMN IF NOT EXISTS google_email VARCHAR(320)"))
        conn.execute(text("ALTER TABLE IF EXISTS blog.integracoes ADD COLUMN IF NOT EXISTS google_access_token BYTEA"))
        conn.execute(text("ALTER TABLE IF EXISTS blog.integracoes ADD COLUMN IF NOT EXISTS google_refresh_token BYTEA"))
        conn.execute(text("ALTER TABLE IF EXISTS blog.integracoes ADD COLUMN IF NOT EXISTS google_token_expira_em TIMESTAMPTZ"))
    Base.metadata.create_all(engine)
    task = asyncio.create_task(executar_agenda(settings.scheduler_interval_seconds))
    yield
    task.cancel()


app = FastAPI(title="Blog Service", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "blog-service"}
