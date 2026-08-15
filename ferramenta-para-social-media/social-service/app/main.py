from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.clientes_routes import router as clientes_router
from app.oauth_routes import router as oauth_router
from app.routes import router


app = FastAPI(title="Social Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins_list, allow_credentials=True,
                   allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], allow_headers=["Authorization", "Content-Type"])
app.include_router(router)
app.include_router(oauth_router)
app.include_router(clientes_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "social-service"}
