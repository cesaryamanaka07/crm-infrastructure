import asyncio
import logging
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import select

from app.config import settings
from app.crypto import criptografar, descriptografar
from app.database import SessionLocal
from app.models import SocialConnection


logger = logging.getLogger("uvicorn.error")


async def renovar_token_instagram(token: str) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            f"{settings.instagram_graph_base_url.rstrip('/')}/refresh_access_token",
            params={"grant_type": "ig_refresh_token", "access_token": token},
        )
    if response.status_code >= 400:
        detalhe = "token recusado pelo Instagram"
        try: detalhe = response.json().get("error", {}).get("message", detalhe)
        except ValueError: pass
        raise ValueError(detalhe)
    data = response.json()
    if not data.get("access_token") or not data.get("expires_in"):
        raise ValueError("Instagram não retornou um token renovado completo")
    return data


async def renovar_tokens_proximos_do_vencimento():
    agora = datetime.now(timezone.utc)
    limite = agora + timedelta(days=max(settings.instagram_refresh_before_days, 1))
    with SessionLocal() as db:
        conexoes = db.scalars(select(SocialConnection).where(
            SocialConnection.provider == "instagram",
            SocialConnection.expira_em.is_not(None),
            SocialConnection.expira_em > agora,
            SocialConnection.expira_em <= limite,
        )).all()
        for conexao in conexoes:
            try:
                data = await renovar_token_instagram(descriptografar(conexao.access_token))
                conexao.access_token = criptografar(data["access_token"])
                conexao.expira_em = datetime.now(timezone.utc) + timedelta(seconds=int(data["expires_in"]))
                db.commit()
                logger.info("instagram_token_renovado conexao_id=%s expira_em=%s", conexao.id, conexao.expira_em)
            except Exception as erro:
                db.rollback()
                logger.warning("instagram_token_renovacao_falhou conexao_id=%s erro=%s", conexao.id, str(erro)[:180])


async def executar_renovacao_automatica():
    while True:
        try: await renovar_tokens_proximos_do_vencimento()
        except Exception: logger.exception("instagram_token_rotina_falhou")
        await asyncio.sleep(max(settings.token_refresh_interval_seconds, 900))
