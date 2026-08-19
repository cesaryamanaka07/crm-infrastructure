from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from uuid import UUID
import httpx
from jose import JWTError, jwt
from sqlalchemy import select
from app.config import settings
from app.google_calendar import criptografar
from app.models import AutomationSettings

SCOPES = "openid email https://www.googleapis.com/auth/calendar"

def url_autorizacao(usuario_id: UUID, cliente_id: UUID):
    if not settings.google_oauth_client_id or not settings.google_oauth_client_secret or not settings.google_oauth_redirect_uri:
        raise ValueError("Configure GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET e GOOGLE_OAUTH_REDIRECT_URI")
    state = jwt.encode({"sub": str(usuario_id), "cliente_id": str(cliente_id), "exp": datetime.now(timezone.utc) + timedelta(minutes=10)}, settings.secret_key, algorithm=settings.algorithm)
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({"client_id": settings.google_oauth_client_id,
        "redirect_uri": settings.google_oauth_redirect_uri, "response_type": "code", "scope": SCOPES,
        "access_type": "offline", "prompt": "consent select_account", "include_granted_scopes": "true", "state": state})

def ler_state(state: str):
    try:
        dados = jwt.decode(state, settings.secret_key, algorithms=[settings.algorithm])
        return UUID(dados["sub"]), UUID(dados["cliente_id"])
    except (JWTError, KeyError, ValueError) as erro: raise ValueError("Estado OAuth inválido ou expirado") from erro

async def concluir_oauth(db, code: str, state: str):
    usuario_id, cliente_id = ler_state(state)
    async with httpx.AsyncClient(timeout=30) as client:
        resposta = await client.post("https://oauth2.googleapis.com/token", data={"code": code,
            "client_id": settings.google_oauth_client_id, "client_secret": settings.google_oauth_client_secret,
            "redirect_uri": settings.google_oauth_redirect_uri, "grant_type": "authorization_code"})
        if resposta.status_code >= 400: raise ValueError(resposta.json().get("error_description", "Google recusou a autorização"))
        tokens = resposta.json()
        perfil = await client.get("https://openidconnect.googleapis.com/v1/userinfo", headers={"Authorization": f"Bearer {tokens['access_token']}"})
        if perfil.status_code >= 400: raise ValueError("Não foi possível identificar a conta Google")
    config = db.scalar(select(AutomationSettings).where(AutomationSettings.usuario_id == usuario_id, AutomationSettings.cliente_id == cliente_id))
    if not config:
        config = AutomationSettings(usuario_id=usuario_id, cliente_id=cliente_id, cores={}, crm_config={}); db.add(config)
    config.google_email = perfil.json().get("email")
    config.google_calendar_id = "primary"
    config.google_access_token = criptografar(tokens["access_token"])
    if tokens.get("refresh_token"): config.google_refresh_token = criptografar(tokens["refresh_token"])
    config.google_token_expira_em = datetime.now(timezone.utc) + timedelta(seconds=tokens.get("expires_in", 3600))
    db.commit(); return config
