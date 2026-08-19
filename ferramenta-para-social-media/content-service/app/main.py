from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import router
from app.brand_routes import router as brand_router
from app.media_routes import router as media_router
from app.arsenal_routes import router as arsenal_router
from app.strategy_routes import router as strategy_router


app = FastAPI(
    title="Content Service",
    description="Gerencia briefings e o ciclo editorial dos conteúdos",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(router)
app.include_router(brand_router)
app.include_router(media_router)
app.include_router(arsenal_router)
app.include_router(strategy_router)


@app.get("/health", tags=["infraestrutura"])
def health_check():
    return {"status": "ok", "service": "content-service"}
