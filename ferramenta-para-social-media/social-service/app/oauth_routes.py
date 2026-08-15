import logging
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth import obter_usuario_id
from app.config import settings
from app.database import get_db
from app.oauth import (
    PROVIDERS,
    consumir_state,
    criar_url,
    obter_contas_instagram_facebook,
    obter_paginas_facebook,
    obter_perfil,
    salvar_conexao,
    trocar_codigo,
)
from app.models import Cliente


router = APIRouter(prefix="/oauth", tags=["OAuth"])
logger = logging.getLogger("uvicorn.error")


class InicioOAuth(BaseModel):
    cliente_id: str


def _voltar_ao_frontend(provider: str, *, conectado: bool = False, erro: str = ""):
    parametros = {"conectado": provider} if conectado else {
        "erro": erro[:180] or "Não foi possível concluir a autorização",
        "rede": provider,
    }
    destino = f"{settings.frontend_return_url}?{urlencode(parametros)}"
    return RedirectResponse(destino, status_code=303)


@router.post("/{provider}/iniciar")
def iniciar_oauth(
    provider: str,
    dados: InicioOAuth,
    usuario_id=Depends(obter_usuario_id),
    db: Session = Depends(get_db),
):
    """Cria um state de uso único e devolve a tela oficial de autorização."""
    try:
        from uuid import UUID
        cliente_id = UUID(dados.cliente_id)
    except ValueError as erro:
        raise HTTPException(status_code=422, detail="Cliente inválido") from erro
    cliente = db.scalar(select(Cliente).where(Cliente.id == cliente_id, Cliente.usuario_id == usuario_id))
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    logger.info("oauth_inicio provider=%s", provider)
    return {"authorization_url": criar_url(provider, usuario_id, cliente_id, db)}


@router.get("/{provider}/callback", name="oauth_callback")
async def receber_callback_oauth(
    provider: str,
    state: str = "",
    code: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    db: Session = Depends(get_db),
):
    """Recebe o retorno do provedor, troca o code por token e salva a conexão."""
    if provider not in PROVIDERS:
        raise HTTPException(status_code=404, detail="Rede social não suportada")

    if error or not code:
        logger.warning("oauth_callback_recusado provider=%s error=%s", provider, error or "sem_codigo")
        motivo = error_description or error
        if not motivo:
            motivo = "O provedor não retornou o código de autorização; verifique a configuração do Login for Business"
        return _voltar_ao_frontend(
            provider,
            erro=motivo,
        )

    try:
        registro = consumir_state(provider, state, db)
        token = await trocar_codigo(provider, code)
        access_token = token.get("access_token")
        if not access_token:
            raise HTTPException(status_code=502, detail="O provedor não retornou o token de acesso")

        if provider == "facebook":
            paginas = await obter_paginas_facebook(access_token)
            if not paginas:
                raise HTTPException(
                    status_code=422,
                    detail="Nenhuma Página do Facebook foi encontrada nessa conta",
                )
            for pagina in paginas:
                page_token = pagina.get("access_token")
                if page_token:
                    salvar_conexao(
                        db=db,
                        usuario_id=registro.usuario_id,
                        cliente_id=registro.cliente_id,
                        provider="facebook",
                        external_id=str(pagina["id"]),
                        nome=pagina.get("name") or "Página do Facebook",
                        access_token=page_token,
                        refresh_token=None,
                        scopes=token.get("scope", ""),
                        expires_in=token.get("expires_in"),
                    )
        elif provider == "instagram" and settings.instagram_auth_mode == "facebook":
            contas = await obter_contas_instagram_facebook(access_token)
            if not contas:
                raise HTTPException(
                    status_code=422,
                    detail="Nenhuma conta profissional do Instagram vinculada a uma Página foi encontrada",
                )
            for conta in contas:
                salvar_conexao(
                    db=db,
                    usuario_id=registro.usuario_id,
                    cliente_id=registro.cliente_id,
                    provider="instagram",
                    external_id=conta["id"],
                    nome=conta["nome"],
                    access_token=conta["access_token"],
                    refresh_token=None,
                    scopes=token.get("scope", ""),
                    expires_in=token.get("expires_in"),
                )
        else:
            external_id, nome = await obter_perfil(provider, access_token)
            salvar_conexao(
                db=db,
                usuario_id=registro.usuario_id,
                cliente_id=registro.cliente_id,
                provider=provider,
                external_id=external_id,
                nome=nome,
                access_token=access_token,
                refresh_token=token.get("refresh_token"),
                scopes=token.get("scope", ""),
                expires_in=token.get("expires_in"),
            )
    except HTTPException as exc:
        logger.warning("oauth_processamento_falhou provider=%s status=%s", provider, exc.status_code)
        return _voltar_ao_frontend(provider, erro=str(exc.detail))
    except (httpx.HTTPError, KeyError, ValueError):
        logger.exception("oauth_resposta_invalida provider=%s", provider)
        return _voltar_ao_frontend(provider, erro="Resposta inválida ou indisponível do provedor")

    logger.info("oauth_conectado provider=%s", provider)
    return _voltar_ao_frontend(provider, conectado=True)
