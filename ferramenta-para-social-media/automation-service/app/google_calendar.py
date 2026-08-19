import base64
import hashlib
import json
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import httpx
from cryptography.fernet import Fernet
from jose import jwt
from sqlalchemy import text

from app.config import settings


_fernet = Fernet(base64.urlsafe_b64encode(hashlib.sha256(settings.secret_key.encode()).digest()))


def _descriptografar(valor):
    return _fernet.decrypt(bytes(valor)).decode() if valor else None

def criptografar(valor):
    return _fernet.encrypt(valor.encode()) if valor else None


def obter_credencial_blog(db, usuario_id, cliente_id):
    row = db.execute(text("SELECT google_conta_servico FROM blog.integracoes WHERE usuario_id=:u AND cliente_id=:c"), {"u": usuario_id, "c": cliente_id}).first()
    if not row or not row[0]:
        raise ValueError("Configure primeiro o JSON Google em Artigos de Blog > Integrações para este cliente")
    return json.loads(_descriptografar(row[0]))


async def _token(info):
    agora = int(time.time())
    assertion = jwt.encode({"iss": info["client_email"], "scope": "https://www.googleapis.com/auth/calendar",
                            "aud": info.get("token_uri", "https://oauth2.googleapis.com/token"), "iat": agora, "exp": agora + 3600},
                           info["private_key"], algorithm="RS256")
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(info.get("token_uri", "https://oauth2.googleapis.com/token"), data={"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": assertion})
        if response.status_code >= 400:
            try: detalhe = response.json().get("error_description") or response.json().get("error")
            except ValueError: detalhe = "Não foi possível autenticar a conta de serviço"
            raise ValueError(str(detalhe))
        return response.json()["access_token"]

async def _token_oauth(db, config):
    agora = datetime.now(timezone.utc)
    expira = config.google_token_expira_em
    if expira and expira.tzinfo is None: expira = expira.replace(tzinfo=timezone.utc)
    if config.google_access_token and expira and expira > agora + timedelta(minutes=2):
        return _descriptografar(config.google_access_token)
    if not config.google_refresh_token: raise ValueError("Reconecte a conta Google deste cliente")
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post("https://oauth2.googleapis.com/token", data={
            "client_id": settings.google_oauth_client_id, "client_secret": settings.google_oauth_client_secret,
            "refresh_token": _descriptografar(config.google_refresh_token), "grant_type": "refresh_token"})
    if response.status_code >= 400: raise ValueError("A autorização Google expirou ou foi revogada. Reconecte a conta")
    dados = response.json(); config.google_access_token = criptografar(dados["access_token"])
    config.google_token_expira_em = agora + timedelta(seconds=dados.get("expires_in", 3600)); db.commit()
    return dados["access_token"]


async def requisicao(db, usuario_id, cliente_id, calendar_id, metodo, caminho="", **kwargs):
    from app.models import AutomationSettings
    from sqlalchemy import select
    config = db.scalar(select(AutomationSettings).where(AutomationSettings.usuario_id == usuario_id, AutomationSettings.cliente_id == cliente_id))
    central=db.execute(text("SELECT access_token,refresh_token,expira_em FROM social.google_conexoes WHERE usuario_id=:u AND cliente_id=:c"),{"u":usuario_id,"c":cliente_id}).mappings().first()
    if central:
        agora=datetime.now(timezone.utc); exp=central["expira_em"]; exp=exp.replace(tzinfo=timezone.utc) if exp and exp.tzinfo is None else exp
        if exp and exp>agora+timedelta(minutes=2): token=_descriptografar(central["access_token"])
        else:
            async with httpx.AsyncClient(timeout=30) as client: resposta=await client.post("https://oauth2.googleapis.com/token",data={"client_id":settings.google_oauth_client_id,"client_secret":settings.google_oauth_client_secret,"refresh_token":_descriptografar(central["refresh_token"]),"grant_type":"refresh_token"})
            if resposta.status_code>=400: raise ValueError("Reconecte a conta Google no cadastro do cliente")
            dados=resposta.json(); token=dados["access_token"]; db.execute(text("UPDATE social.google_conexoes SET access_token=:a,expira_em=:e WHERE usuario_id=:u AND cliente_id=:c"),{"a":criptografar(token),"e":agora+timedelta(seconds=dados.get("expires_in",3600)),"u":usuario_id,"c":cliente_id});db.commit()
        calendar_id="primary"
    elif config and config.google_refresh_token:
        token = await _token_oauth(db, config); calendar_id = calendar_id or "primary"
    else:
        info = obter_credencial_blog(db, usuario_id, cliente_id); token = await _token(info)
    url = f"https://www.googleapis.com/calendar/v3/calendars/{quote(calendar_id, safe='')}{caminho}"
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.request(metodo, url, headers={"Authorization": f"Bearer {token}"}, **kwargs)
    if response.status_code >= 400:
        try: detalhe = response.json().get("error", {}).get("message", "Google Agenda recusou a operação")
        except ValueError: detalhe = "Google Agenda recusou a operação"
        raise ValueError(detalhe)
    return response.json() if response.content else None


def payload_evento(atividade):
    fim = atividade.fim_em or (atividade.inicio_em + timedelta(hours=1))
    return {"summary": atividade.titulo, "description": atividade.descricao or "",
            "start": {"dateTime": atividade.inicio_em.isoformat(), "timeZone": "America/Sao_Paulo"},
            "end": {"dateTime": fim.isoformat(), "timeZone": "America/Sao_Paulo"},
            "attendees": [{"email": email} for email in (atividade.convidados or [])],
            "extendedProperties": {"private": {"origem": "social-media-crm", "atividade_id": str(atividade.id), "tipo": atividade.tipo}}}


async def criar_evento(db, usuario_id, atividade, calendar_id):
    return await requisicao(db, usuario_id, atividade.cliente_id, calendar_id, "POST", "/events", params={"sendUpdates": "all"}, json=payload_evento(atividade))


async def atualizar_evento(db, usuario_id, atividade, calendar_id):
    return await requisicao(db, usuario_id, atividade.cliente_id, calendar_id, "PUT", f"/events/{quote(atividade.google_event_id, safe='')}", params={"sendUpdates": "all"}, json=payload_evento(atividade))


async def excluir_evento(db, usuario_id, atividade, calendar_id):
    if atividade.google_event_id:
        await requisicao(db, usuario_id, atividade.cliente_id, calendar_id, "DELETE", f"/events/{quote(atividade.google_event_id, safe='')}", params={"sendUpdates": "all"})


async def listar_eventos(db, usuario_id, cliente_id, calendar_id, inicio, fim):
    data = await requisicao(db, usuario_id, cliente_id, calendar_id, "GET", "/events", params={"timeMin": inicio.isoformat(), "timeMax": fim.isoformat(), "singleEvents": "true", "orderBy": "startTime", "maxResults": 2500})
    return data.get("items", [])
