import hashlib
import hmac
import logging

from fastapi import APIRouter, Header, HTTPException, Query, Request, Response, status

from app.config import settings


router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)


@router.get("/meta", response_class=Response)
def verificar_webhook_meta(
    mode: str | None = Query(default=None, alias="hub.mode"),
    verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    challenge: str | None = Query(default=None, alias="hub.challenge"),
):
    """Responde ao desafio usado pela Meta ao cadastrar a URL de callback."""
    token_configurado = settings.meta_webhook_verify_token
    if not token_configurado:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Token de verificação do webhook não configurado",
        )
    if mode != "subscribe" or not hmac.compare_digest(verify_token or "", token_configurado):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verificação recusada")
    if challenge is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Desafio ausente")
    return Response(content=challenge, media_type="text/plain", status_code=200)


@router.post("/meta", status_code=200)
async def receber_webhook_meta(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
):
    """Valida a assinatura antes de aceitar eventos do Facebook/Instagram."""
    segredo = settings.meta_client_secret
    if not segredo:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Segredo do aplicativo Meta não configurado",
        )

    corpo = await request.body()
    assinatura_esperada = "sha256=" + hmac.new(
        segredo.encode("utf-8"), corpo, hashlib.sha256
    ).hexdigest()
    if not x_hub_signature_256 or not hmac.compare_digest(
        x_hub_signature_256, assinatura_esperada
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Assinatura inválida")

    try:
        evento = await request.json()
    except ValueError as erro:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="JSON inválido") from erro

    objeto = evento.get("object", "desconhecido") if isinstance(evento, dict) else "desconhecido"
    entradas = evento.get("entry", []) if isinstance(evento, dict) else []
    logger.info("Webhook Meta validado: objeto=%s entradas=%d", objeto, len(entradas))

    # A Meta exige resposta rápida. O processamento de comentários e mensagens
    # será encaminhado para a fila do executor de automações na próxima etapa.
    return {"status": "EVENT_RECEIVED"}


@router.get("/meta/status")
def status_webhook_meta():
    return {
        "status": "pronto" if settings.meta_webhook_verify_token else "configuracao_pendente",
        "assinatura_ativa": bool(settings.meta_client_secret),
    }
