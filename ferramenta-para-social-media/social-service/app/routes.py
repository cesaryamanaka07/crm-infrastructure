import asyncio
from datetime import datetime, timedelta, timezone
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.auth import obter_usuario_id
from app.config import settings
from app.crypto import descriptografar
from app.database import get_db
from app.models import SocialConnection


router = APIRouter()


class InsightsEntrada(BaseModel):
    conexao_ids: list[UUID] = Field(min_length=1, max_length=50)


async def _get_json(client: httpx.AsyncClient, url: str, params: dict) -> dict:
    response = await client.get(url, params=params)
    if response.status_code >= 400:
        detalhe = "Métrica não liberada pela rede social"
        try:
            detalhe = response.json().get("error", {}).get("message", detalhe)
        except ValueError:
            pass
        if "Unsupported request - method type:" in detalhe:
            detalhe = (
                "A Meta autorizou o login, mas bloqueou a leitura desta conta externa. "
                "Adicione a conta como Instagram Tester e aceite o convite, ou obtenha "
                "Acesso Avançado para as permissões do Instagram."
            )
        elif "Error validating access token" in detalhe or "Session has expired" in detalhe:
            detalhe = "A autorização expirou ou foi revogada pela Meta. Reconecte esta conta do Instagram."
        raise ValueError(detalhe)
    return response.json()


async def _insights_instagram(client: httpx.AsyncClient, conexao: SocialConnection, token: str) -> dict:
    bases = [settings.facebook_graph_base_url.rstrip("/"), settings.instagram_graph_base_url.rstrip("/")]
    versao = settings.instagram_api_version or settings.meta_api_version
    perfil = None
    base_ativa = ""
    ultimo_erro = "Conta do Instagram indisponível"
    for base in bases:
        try:
            perfil = await _get_json(client, f"{base}/{versao}/{conexao.external_id}", {
                "fields": "id,username,name,followers_count,follows_count,media_count", "access_token": token,
            })
            base_ativa = base
            break
        except ValueError as erro:
            ultimo_erro = str(erro)
    if perfil is None:
        raise ValueError(ultimo_erro)
    metricas = {"seguidores": perfil.get("followers_count"), "seguindo": perfil.get("follows_count"),
                "publicacoes": perfil.get("media_count")}

    async def buscar(nome: str):
        try:
            data = await _get_json(client, f"{base_ativa}/{versao}/{conexao.external_id}/insights", {
                "metric": nome, "period": "day", "metric_type": "total_value", "access_token": token,
            })
            item = (data.get("data") or [{}])[0]
            valor = item.get("total_value", {}).get("value")
            if valor is None and item.get("values"):
                valor = item["values"][-1].get("value")
            return nome, valor
        except ValueError:
            return nome, None

    nomes = ["reach", "views", "profile_views", "accounts_engaged", "total_interactions"]
    for nome, valor in await asyncio.gather(*(buscar(nome) for nome in nomes)):
        metricas[nome] = valor
    midias = await _get_json(client, f"{base_ativa}/{versao}/{conexao.external_id}/media", {
        "fields": "id,caption,media_type,media_product_type,permalink,timestamp,like_count,comments_count,media_url,thumbnail_url",
        "limit": 50, "access_token": token,
    })
    melhores = []
    for item in midias.get("data", []):
        curtidas = item.get("like_count") or 0
        comentarios = item.get("comments_count") or 0
        produto = item.get("media_product_type") or item.get("media_type") or "POST"
        tipo = "Reels" if produto == "REELS" else "Carrossel" if item.get("media_type") == "CAROUSEL_ALBUM" else "Post"
        melhores.append({"id": item.get("id"), "tipo": tipo, "titulo": (item.get("caption") or "Sem legenda")[:140],
                         "url": item.get("permalink"), "publicado_em": item.get("timestamp"),
                         "thumbnail_url": item.get("thumbnail_url") or item.get("media_url"),
                         "curtidas": curtidas, "comentarios": comentarios, "compartilhamentos": None,
                         "alcance": None, "pontuacao": curtidas + comentarios * 2})
    melhores.sort(key=lambda item: item["pontuacao"], reverse=True)
    return {"nome": perfil.get("username") or perfil.get("name") or conexao.nome,
            "metricas": metricas, "melhores_conteudos": melhores[:5]}


async def _insights_facebook_page(client: httpx.AsyncClient, conexao: SocialConnection, token: str) -> dict:
    base = settings.facebook_graph_base_url.rstrip("/")
    versao = settings.facebook_api_version or settings.meta_api_version
    perfil = await _get_json(client, f"{base}/{versao}/{conexao.external_id}", {
        "fields": "id,name,fan_count,followers_count", "access_token": token,
    })
    metricas = {"curtidas_pagina": perfil.get("fan_count"), "seguidores": perfil.get("followers_count")}

    async def buscar(nome: str):
        try:
            data = await _get_json(client, f"{base}/{versao}/{conexao.external_id}/insights", {
                "metric": nome, "period": "day", "access_token": token,
            })
            item = (data.get("data") or [{}])[0]
            valor = item.get("values", [{}])[-1].get("value") if item.get("values") else None
            return nome, valor
        except ValueError:
            return nome, None

    nomes = ["page_impressions", "page_post_engagements", "page_views_total"]
    for nome, valor in await asyncio.gather(*(buscar(nome) for nome in nomes)):
        metricas[nome] = valor
    posts = await _get_json(client, f"{base}/{versao}/{conexao.external_id}/published_posts", {
        "fields": "id,message,created_time,permalink_url,full_picture,shares,likes.limit(0).summary(true),comments.limit(0).summary(true),attachments.limit(1){media_type,type}",
        "limit": 50, "access_token": token,
    })
    melhores = []
    for item in posts.get("data", []):
        curtidas = item.get("likes", {}).get("summary", {}).get("total_count", 0)
        comentarios = item.get("comments", {}).get("summary", {}).get("total_count", 0)
        compartilhamentos = item.get("shares", {}).get("count", 0)
        anexo = (item.get("attachments", {}).get("data") or [{}])[0]
        tipo_anexo = f"{anexo.get('media_type', '')} {anexo.get('type', '')}".lower()
        tipo = "Reels" if "video" in tipo_anexo else "Carrossel" if "album" in tipo_anexo or "multi" in tipo_anexo else "Post"
        melhores.append({"id": item.get("id"), "tipo": tipo, "titulo": (item.get("message") or "Publicação sem texto")[:140],
                         "url": item.get("permalink_url"), "publicado_em": item.get("created_time"),
                         "thumbnail_url": item.get("full_picture"),
                         "curtidas": curtidas, "comentarios": comentarios, "compartilhamentos": compartilhamentos,
                         "alcance": None, "pontuacao": curtidas + comentarios * 2 + compartilhamentos * 3})
    melhores.sort(key=lambda item: item["pontuacao"], reverse=True)
    return {"nome": perfil.get("name") or conexao.nome, "metricas": metricas, "melhores_conteudos": melhores[:5]}


async def _insights_linkedin(client: httpx.AsyncClient, conexao: SocialConnection, token: str) -> dict:
    headers = {"Authorization": f"Bearer {token}", "LinkedIn-Version": settings.linkedin_api_version,
               "X-Restli-Protocol-Version": "2.0.0", "Content-Type": "application/json"}

    async def buscar(tipo: str):
        response = await client.get("https://api.linkedin.com/rest/memberCreatorPostAnalytics", headers=headers,
                                    params={"q": "me", "queryType": tipo, "aggregation": "TOTAL"})
        if response.status_code >= 400:
            raise ValueError("O LinkedIn exige a permissão aprovada r_member_postAnalytics para exibir insights.")
        return sum(item.get("count", 0) for item in response.json().get("elements", []))

    tipos = {"impressoes": "IMPRESSION", "alcance": "MEMBERS_REACHED", "reacoes": "REACTION",
             "comentarios": "COMMENT", "compartilhamentos": "RESHARE"}
    valores = await asyncio.gather(*(buscar(tipo) for tipo in tipos.values()))
    return {"nome": conexao.nome, "metricas": dict(zip(tipos.keys(), valores)), "melhores_conteudos": []}


@router.get("/conexoes")
def listar_conexoes(usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    itens = db.scalars(select(SocialConnection).where(SocialConnection.usuario_id == usuario_id)).all()
    limite_temporario = datetime.now(timezone.utc) + timedelta(hours=2)
    return [{"id": str(item.id), "provider": item.provider, "nome": item.nome,
             "cliente_id": str(item.cliente_id) if item.cliente_id else None,
             "external_id": item.external_id, "expira_em": item.expira_em,
             "tipo_token": "temporario" if item.provider == "instagram" and (item.expira_em is None or item.expira_em <= limite_temporario) else "renovavel",
             "conectado_em": item.conectado_em, "selecionada": item.selecionada} for item in itens]


@router.post("/insights")
async def obter_insights(dados: InsightsEntrada, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    conexoes = db.scalars(select(SocialConnection).where(
        SocialConnection.usuario_id == usuario_id, SocialConnection.id.in_(dados.conexao_ids),
    )).all()
    mapa = {item.id: item for item in conexoes}
    resultados = []
    async with httpx.AsyncClient(timeout=25) as client:
        for conexao_id in dados.conexao_ids:
            conexao = mapa.get(conexao_id)
            if conexao is None:
                continue
            base = {"id": str(conexao.id), "cliente_id": str(conexao.cliente_id), "provider": conexao.provider,
                    "nome": conexao.nome, "external_id": conexao.external_id}
            if conexao.provider == "facebook_profile":
                resultados.append({**base, "status": "indisponivel", "metricas": {},
                                   "erro": "A Meta não fornece insights de perfis pessoais pela API."})
                continue
            try:
                token = descriptografar(conexao.access_token)
                if not token:
                    raise ValueError("Token da conexão não encontrado")
                if conexao.provider == "instagram":
                    dados_rede = await _insights_instagram(client, conexao, token)
                elif conexao.provider == "facebook_page":
                    dados_rede = await _insights_facebook_page(client, conexao, token)
                elif conexao.provider == "linkedin":
                    dados_rede = await _insights_linkedin(client, conexao, token)
                else:
                    raise ValueError("Insights ainda não suportados para esta rede")
                resultados.append({**base, **dados_rede, "status": "ok"})
            except (ValueError, httpx.HTTPError) as erro:
                resultados.append({**base, "status": "erro", "metricas": {}, "erro": str(erro)[:240]})
    return resultados


@router.put("/conexoes/{conexao_id}/selecionar")
def selecionar_conexao(conexao_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    conexao = db.scalar(select(SocialConnection).where(
        SocialConnection.id == conexao_id,
        SocialConnection.usuario_id == usuario_id,
    ))
    if conexao is None:
        raise HTTPException(status_code=404, detail="Conexão não encontrada")
    db.execute(update(SocialConnection).where(
        SocialConnection.usuario_id == usuario_id,
        SocialConnection.cliente_id == conexao.cliente_id,
        SocialConnection.provider == conexao.provider,
    ).values(selecionada=False))
    conexao.selecionada = True
    db.commit()
    return {"id": str(conexao.id), "provider": conexao.provider, "selecionada": True}


@router.delete("/conexoes/{conexao_id}", status_code=204)
def desconectar(conexao_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    conexao = db.scalar(select(SocialConnection).where(SocialConnection.id == conexao_id, SocialConnection.usuario_id == usuario_id))
    if conexao is None:
        raise HTTPException(status_code=404, detail="Conexão não encontrada")
    provider = conexao.provider
    era_selecionada = conexao.selecionada
    db.delete(conexao)
    db.flush()
    if era_selecionada:
        substituta = db.scalar(select(SocialConnection).where(
            SocialConnection.usuario_id == usuario_id,
            SocialConnection.cliente_id == conexao.cliente_id,
            SocialConnection.provider == provider,
        ).order_by(SocialConnection.conectado_em))
        if substituta:
            substituta.selecionada = True
    db.commit()
