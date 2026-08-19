from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.n8n_routes import router as n8n_router
from app.routes import router

app = FastAPI(title="Automation Service", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(router)
app.include_router(n8n_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "automation-service"}
