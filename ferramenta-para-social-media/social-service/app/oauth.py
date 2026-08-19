import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from uuid import UUID

import httpx
from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import settings
from app.crypto import criptografar
from app.models import OAuthState, SocialConnection


PROVIDERS = {"facebook", "facebook_page", "facebook_profile", "instagram", "instagram_facebook", "linkedin"}


def _hash_state(state: str) -> str:
    return hashlib.sha256(state.encode()).hexdigest()


def criar_url(provider: str, usuario_id: UUID, cliente_id: UUID, db: Session) -> str:
    if provider not in PROVIDERS:
        raise HTTPException(status_code=404, detail="Rede social não suportada")
    if provider in {"facebook", "facebook_page", "facebook_profile", "instagram", "instagram_facebook"} and (
        not settings.client_id(provider)
        or not settings.client_secret(provider)
        or not settings.api_version(provider)
    ):
        nome = "Instagram" if provider in {"instagram", "instagram_facebook"} else "Facebook"
        raise HTTPException(status_code=503, detail=f"Aplicativo {nome} não configurado")
    if provider in {"facebook", "facebook_page"} and not settings.facebook_scopes:
        raise HTTPException(status_code=503, detail="Permissões do Facebook não configuradas")
    if provider == "instagram" and not settings.instagram_scopes:
        raise HTTPException(status_code=503, detail="Permissões do Instagram não configuradas")
    if provider == "instagram_facebook" and not settings.facebook_scopes:
        raise HTTPException(status_code=503, detail="Permissões Meta para Instagram não configuradas")
    if provider == "linkedin" and (
        not settings.linkedin_client_id or not settings.linkedin_client_secret
    ):
        raise HTTPException(status_code=503, detail="Aplicativo LinkedIn não configurado")
    if not settings.provider_endpoints_configured(provider):
        raise HTTPException(status_code=503, detail=f"Endpoints do {provider} não configurados")
    state = secrets.token_urlsafe(40)
    db.add(OAuthState(
        state_hash=_hash_state(state), usuario_id=usuario_id, cliente_id=cliente_id, provider=provider,
        expira_em=datetime.now(timezone.utc) + timedelta(minutes=10),
    ))
    db.commit()

    if provider in {"facebook", "facebook_page", "facebook_profile", "instagram_facebook"}:
        params = {
            "client_id": settings.client_id(provider),
            "redirect_uri": settings.callback_url(provider),
            "state": state,
            "response_type": "code",
            "override_default_response_type": "true",
            "scope": settings.facebook_profile_scopes if provider == "facebook_profile" else settings.facebook_scopes,
        }
        if settings.login_config_id(provider):
            params["config_id"] = settings.login_config_id(provider)
            params.pop("scope", None)
        base_url = settings.facebook_authorization_base_url.rstrip("/")
        return f"{base_url}/{settings.api_version(provider)}/dialog/oauth?{urlencode(params)}"

    if provider == "instagram":
        params = {
            "client_id": settings.client_id(provider),
            "redirect_uri": settings.callback_url(provider),
            "state": state,
            "response_type": "code",
            "scope": settings.instagram_scopes,
        }
        params["enable_fb_login"] = "0"
        params["force_authentication"] = "1"
        return f"{settings.instagram_authorization_url}?{urlencode(params)}"

    params = {
        "response_type": "code", "client_id": settings.linkedin_client_id,
        "redirect_uri": settings.callback_url(provider), "state": state,
        "scope": settings.linkedin_scopes.replace(",", " "),
    }
    return f"{settings.linkedin_authorization_url}?{urlencode(params)}"


def _erro_provedor(provider: str, response: httpx.Response) -> HTTPException:
    detalhe = "autorização recusada"
    try:
        data = response.json()
        erro = data.get("error", data) if isinstance(data, dict) else data
        if isinstance(erro, dict):
            detalhe = erro.get("message") or erro.get("error_description") or detalhe
        elif isinstance(erro, str):
            detalhe = data.get("error_description", erro) if isinstance(data, dict) else erro
    except ValueError:
        pass
    return HTTPException(status_code=502, detail=f"{provider}: {str(detalhe)[:180]}")


def consumir_state(provider: str, state: str, db: Session) -> OAuthState:
    registro = db.scalar(select(OAuthState).where(
        OAuthState.state_hash == _hash_state(state), OAuthState.provider == provider,
    ))
    agora = datetime.now(timezone.utc)
    if registro is None or registro.expira_em < agora:
        raise HTTPException(status_code=400, detail="Estado OAuth inválido ou expirado")
    db.delete(registro)
    db.commit()
    return registro


def salvar_conexao(
    db: Session, usuario_id: UUID, cliente_id: UUID, provider: str, external_id: str, nome: str,
    access_token: str, refresh_token: str | None, scopes: str, expires_in: int | None,
):
    conexao = db.scalar(select(SocialConnection).where(
        SocialConnection.usuario_id == usuario_id,
        SocialConnection.provider == provider,
        SocialConnection.external_id == external_id,
    ))
    if conexao is None:
        ja_existe_selecionada = db.scalar(select(SocialConnection.id).where(
            SocialConnection.usuario_id == usuario_id,
            SocialConnection.cliente_id == cliente_id,
            SocialConnection.provider == provider,
            SocialConnection.selecionada.is_(True),
        ))
        conexao = SocialConnection(
            usuario_id=usuario_id,
            cliente_id=cliente_id,
            provider=provider,
            external_id=external_id,
            nome=nome,
            access_token=b"",
            selecionada=ja_existe_selecionada is None,
        )
        db.add(conexao)
    conexao.cliente_id = cliente_id
    conexao.nome = nome
    conexao.access_token = criptografar(access_token)
    conexao.refresh_token = criptografar(refresh_token)
    conexao.scopes = ",".join(scopes) if isinstance(scopes, list) else scopes
    conexao.expira_em = datetime.now(timezone.utc) + timedelta(seconds=expires_in) if expires_in else None
    db.commit()


async def trocar_codigo(provider: str, code: str) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        if provider == "linkedin":
            response = await client.post(settings.linkedin_token_url, data={
                "grant_type": "authorization_code", "code": code,
                "client_id": settings.linkedin_client_id,
                "client_secret": settings.linkedin_client_secret,
                "redirect_uri": settings.callback_url(provider),
            })
        elif provider in {"facebook", "facebook_page", "facebook_profile", "instagram_facebook"}:
            response = await client.get(
                f"{settings.facebook_graph_base_url.rstrip('/')}/{settings.api_version(provider)}/oauth/access_token",
                params={"client_id": settings.client_id(provider), "client_secret": settings.client_secret(provider),
                        "redirect_uri": settings.callback_url(provider), "code": code},
            )
        else:
            response = await client.post(
                settings.instagram_token_url,
                data={
                    "client_id": settings.client_id(provider),
                    "client_secret": settings.client_secret(provider),
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.callback_url(provider),
                    "code": code,
                },
            )
        if response.status_code >= 400:
            raise _erro_provedor(provider, response)
        return response.json()


async def trocar_token_instagram_longa_duracao(token_curto: str) -> dict:
    """Troca o token de aproximadamente uma hora por um token renovável de longa duração."""
    parametros = {
        "grant_type": "ig_exchange_token",
        "client_secret": settings.instagram_client_secret,
        "access_token": token_curto,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{settings.instagram_graph_base_url.rstrip('/')}/access_token",
            data=parametros,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if response.status_code >= 400 and "Unsupported request - method type: post" in response.text:
            response = await client.get(
                f"{settings.instagram_graph_base_url.rstrip('/')}/access_token",
                params=parametros,
            )
    if response.status_code >= 400:
        if "Unsupported request - method type:" in response.text:
            raise HTTPException(
                status_code=403,
                detail=(
                    "A Meta aceitou o login, mas bloqueou o token para esta conta externa. "
                    "Conceda Acesso Avançado às permissões Instagram do aplicativo ou adicione "
                    "a conta como Instagram Tester e aceite o convite antes de reconectar."
                ),
            )
        raise _erro_provedor("instagram", response)
    data = response.json()
    if not data.get("access_token"):
        raise HTTPException(status_code=502, detail="Instagram não retornou o token de longa duração")
    return data


async def obter_perfil(provider: str, access_token: str, external_id: str | None = None) -> tuple[str, str]:
    async with httpx.AsyncClient(timeout=30) as client:
        if provider == "linkedin":
            response = await client.get(settings.linkedin_userinfo_url, headers={"Authorization": f"Bearer {access_token}"})
            if response.status_code >= 400:
                raise _erro_provedor(provider, response)
            data = response.json()
            return str(data["sub"]), data.get("name") or "LinkedIn"
        if provider == "instagram":
            if not external_id:
                raise HTTPException(status_code=502, detail="Instagram não retornou o ID da conta")
            response = await client.get(
                f"{settings.instagram_graph_base_url.rstrip('/')}/{settings.api_version(provider)}/{external_id}",
                params={"fields": "id,user_id,username,name", "access_token": access_token},
            )
            if response.status_code >= 400:
                raise _erro_provedor(provider, response)
            data = response.json()
            return str(data.get("user_id") or data.get("id") or external_id), data.get("username") or data.get("name") or "Instagram"
        response = await client.get(
            f"{settings.facebook_graph_base_url.rstrip('/')}/{settings.api_version(provider)}/me",
            params={"fields": "id,name", "access_token": access_token},
        )
        if response.status_code >= 400:
            raise _erro_provedor(provider, response)
        data = response.json()
        return str(data["id"]), data.get("name") or "Facebook"


async def obter_paginas_facebook(access_token: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            f"{settings.facebook_graph_base_url.rstrip('/')}/{settings.api_version('facebook')}/me/accounts",
            params={
                "fields": "id,name,access_token",
                "access_token": access_token,
            },
        )
        if response.status_code >= 400:
            raise _erro_provedor("facebook", response)
        return response.json().get("data", [])


async def obter_contas_instagram_facebook(access_token: str) -> list[dict]:
    """Lista contas profissionais do Instagram vinculadas às Páginas autorizadas."""
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            f"{settings.facebook_graph_base_url.rstrip('/')}/{settings.api_version('instagram')}/me/accounts",
            params={
                "fields": "id,name,access_token,instagram_business_account{id,username,name}",
                "access_token": access_token,
            },
        )
        if response.status_code >= 400:
            raise _erro_provedor("instagram", response)

        contas = []
        for pagina in response.json().get("data", []):
            instagram = pagina.get("instagram_business_account")
            page_token = pagina.get("access_token")
            if instagram and page_token:
                contas.append({
                    "id": str(instagram["id"]),
                    "nome": instagram.get("username") or instagram.get("name") or pagina.get("name") or "Instagram",
                    "access_token": page_token,
                })
        return contas
