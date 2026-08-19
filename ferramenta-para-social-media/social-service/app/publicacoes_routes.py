import json
import logging
from datetime import datetime, timezone
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import obter_usuario_id
from app.config import settings
from app.crypto import descriptografar
from app.database import get_db
from app.models import SocialConnection
from app.models_publicacoes import Publicacao, PublicacaoIdeia, PublicacaoItem, PublicacaoRede

router = APIRouter(prefix="/publicacoes", tags=["publicações"])
logger = logging.getLogger(__name__)
FORMATOS = {"post_unico", "carrossel", "reels", "story"}
PROVIDERS = {"facebook_page", "instagram", "linkedin"}


def _json(valor, padrao):
    try: return json.loads(valor) if valor else padrao
    except (TypeError, ValueError): return padrao


def _hashtags(valor):
    itens = valor if isinstance(valor, list) else [x for x in str(valor or "").replace(",", " ").split() if x]
    resultado = []
    for item in itens[:5]:
        item = "#" + item.lstrip("#").strip().replace(" ", "_")
        if len(item) > 1 and item.lower() not in {x.lower() for x in resultado}: resultado.append(item)
    return resultado[:5]


def _serializar(item, redes):
    return {"id": str(item.id), "cliente_id": str(item.cliente_id), "formato": item.formato, "titulo": item.titulo, "legenda": item.legenda, "hashtags": item.hashtags, "roteiro": item.roteiro, "duracao_segundos": item.duracao_segundos, "status": item.status, "publicar_em": item.publicar_em, "redes": [{"provider": r.provider, "status": r.status, "erro": r.erro, "external_id": r.external_id} for r in redes]}


@router.get("")
def listar_publicacoes(cliente_id: UUID | None = None, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    consulta = select(Publicacao).where(Publicacao.usuario_id == usuario_id).order_by(Publicacao.criado_em.desc()).limit(100)
    if cliente_id: consulta = consulta.where(Publicacao.cliente_id == cliente_id)
    itens = db.scalars(consulta).all()
    return [_serializar(item, db.scalars(select(PublicacaoRede).where(PublicacaoRede.publicacao_id == item.id)).all()) for item in itens]


@router.get("/midia/{item_id}")
def obter_midia(item_id: UUID, db: Session = Depends(get_db)):
    item = db.get(PublicacaoItem, item_id)
    if not item: raise HTTPException(404, "Arquivo não encontrado")
    return Response(content=item.arquivo, media_type=item.mime_type, headers={"Cache-Control": "public, max-age=86400"})


@router.post("/briefing")
async def gerar_briefing(ideia: str = Form(...), formato: str = Form(...), usuario_id: UUID = Depends(obter_usuario_id)):
    if not settings.omniroute_base_url or not settings.omniroute_api_key: raise HTTPException(503, "OmniRouter não configurado para gerar o briefing")
    prompt = f"""Crie um plano de postagem para a ideia editorial abaixo. Formato: {formato}. Ideia: {ideia}
Responda somente JSON válido em português brasileiro com estas chaves: titulo, prompts (lista de objetos com titulo e prompt; 1 item salvo para post/story/reels e 2 itens para carrossel), legenda, hashtags (exatamente 5 strings com #), roteiro (para reels, uma string com texto falado e sugestões de cena; para os demais, string vazia). Não crie imagens. O prompt deve ser copiável para ChatGPT ou Gemini e descrever composição, formato, iluminação, estilo e texto que deve aparecer."""
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resposta = await client.post(f"{settings.omniroute_base_url.rstrip('/')}/chat/completions", headers={"Authorization": f"Bearer {settings.omniroute_api_key}"}, json={"model": settings.omniroute_text_model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.7})
        if resposta.status_code >= 400: raise HTTPException(502, "OmniRouter recusou a geração automática do briefing")
        conteudo = resposta.json()["choices"][0]["message"]["content"]
        conteudo = conteudo.replace("```json", "").replace("```", "").strip()
        return json.loads(conteudo)
    except HTTPException: raise
    except Exception as erro:
        logger.exception("briefing_postagem_falhou")
        raise HTTPException(502, "Não foi possível gerar o briefing automático da Linha Editorial") from erro


@router.post("")
async def criar_publicacao(
    cliente_id: UUID = Form(...), formato: str = Form(...), titulo: str = Form(""), legenda: str = Form(""), hashtags: str = Form("[]"), redes: str = Form("[]"), publicar_em: str | None = Form(None), roteiro: str = Form(""), duracao_segundos: int | None = Form(None), titulos_itens: str = Form("[]"), prompts_itens: str = Form("[]"), arquivos: list[UploadFile] = File(...), usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    if formato not in FORMATOS: raise HTTPException(422, "Formato de postagem inválido")
    if not arquivos or len(arquivos) > 20: raise HTTPException(422, "Envie pelo menos um arquivo e no máximo 20")
    if formato == "carrossel" and len(arquivos) < 2: raise HTTPException(422, "Um carrossel precisa de pelo menos 2 arquivos")
    if formato == "reels" and any(not (arquivo.content_type or "").startswith("video/") for arquivo in arquivos): raise HTTPException(422, "Reels exige um arquivo de vídeo")
    if formato != "reels" and any(not (arquivo.content_type or "").startswith("image/") for arquivo in arquivos): raise HTTPException(422, "Este formato exige arquivos de imagem")
    try: lista_redes = _json(redes, [])
    except Exception: lista_redes = []
    lista_redes = list(dict.fromkeys(lista_redes))
    if not lista_redes or any(rede not in PROVIDERS for rede in lista_redes): raise HTTPException(422, "Selecione ao menos uma rede social válida")
    conexoes = db.scalars(select(SocialConnection).where(SocialConnection.usuario_id == usuario_id, SocialConnection.cliente_id == cliente_id, SocialConnection.provider.in_(lista_redes), SocialConnection.selecionada.is_(True))).all()
    mapa = {item.provider: item for item in conexoes}
    faltantes = [rede for rede in lista_redes if rede not in mapa]
    if faltantes: raise HTTPException(422, f"Nenhuma conta selecionada para: {', '.join(faltantes)}")
    agendada = None
    if publicar_em:
        try: agendada = datetime.fromisoformat(publicar_em.replace("Z", "+00:00"))
        except ValueError as erro: raise HTTPException(422, "Data de agendamento inválida") from erro
        if agendada <= datetime.now(timezone.utc): raise HTTPException(422, "O agendamento deve ser no futuro")
    if formato == "reels" and (duracao_segundos is None or not 1 <= duracao_segundos <= 90): raise HTTPException(422, "A duração do Reels deve estar entre 1 e 90 segundos")
    titulos = _json(titulos_itens, []); prompts = _json(prompts_itens, [])
    publicacao = Publicacao(usuario_id=usuario_id, cliente_id=cliente_id, formato=formato, titulo=titulo.strip(), legenda=legenda.strip(), hashtags=_hashtags(_json(hashtags, hashtags)), roteiro=roteiro.strip() or None, duracao_segundos=duracao_segundos, publicar_em=agendada, status="agendada" if agendada else "pendente")
    db.add(publicacao); db.flush()
    for ordem, arquivo in enumerate(arquivos):
        conteudo = await arquivo.read()
        if not conteudo: raise HTTPException(422, "Um dos arquivos está vazio")
        db.add(PublicacaoItem(publicacao_id=publicacao.id, ordem=ordem, titulo=str(titulos[ordem]) if ordem < len(titulos) else "", prompt=str(prompts[ordem]) if ordem < len(prompts) else "", arquivo=conteudo, nome_arquivo=arquivo.filename or f"arquivo-{ordem}", mime_type=arquivo.content_type or "application/octet-stream"))
    for rede in lista_redes: db.add(PublicacaoRede(publicacao_id=publicacao.id, provider=rede, conexao_id=mapa[rede].id))
    db.commit(); db.refresh(publicacao)
    if not agendada: await publicar_por_id(publicacao.id, usuario_id, db)
    redes_db = db.scalars(select(PublicacaoRede).where(PublicacaoRede.publicacao_id == publicacao.id)).all()
    return _serializar(publicacao, redes_db)


async def publicar_por_id(publicacao_id: UUID, usuario_id: UUID, db: Session):
    publicacao = db.scalar(select(Publicacao).where(Publicacao.id == publicacao_id, Publicacao.usuario_id == usuario_id))
    if not publicacao: return
    itens = db.scalars(select(PublicacaoItem).where(PublicacaoItem.publicacao_id == publicacao.id).order_by(PublicacaoItem.ordem)).all()
    redes = db.scalars(select(PublicacaoRede).where(PublicacaoRede.publicacao_id == publicacao.id, PublicacaoRede.status.in_(["pendente", "erro"]))).all()
    for rede in redes:
        conexao = db.get(SocialConnection, rede.conexao_id)
        try:
            if rede.provider == "instagram": external = await publicar_instagram(publicacao, itens, conexao)
            elif rede.provider == "facebook_page": external = await publicar_facebook(publicacao, itens, conexao)
            else: external = await publicar_linkedin(publicacao, itens, conexao)
            rede.status = "publicada"; rede.external_id = external; rede.publicado_em = datetime.now(timezone.utc); rede.erro = None
        except Exception as erro:
            rede.status = "erro"; rede.erro = str(erro)[:500]; logger.exception("publicacao_falhou provider=%s", rede.provider)
    estados = [rede.status for rede in db.scalars(select(PublicacaoRede).where(PublicacaoRede.publicacao_id == publicacao.id)).all()]
    publicacao.status = "publicada" if estados and all(x == "publicada" for x in estados) else "parcial" if any(x == "publicada" for x in estados) else "erro"
    db.commit()


async def _url_item(item):
    base = settings.social_public_base_url.rstrip("/")
    if not base: raise RuntimeError("SOCIAL_PUBLIC_BASE_URL não configurada")
    return f"{base}/publicacoes/midia/{item.id}"


async def publicar_instagram(publicacao, itens, conexao):
    token = descriptografar(conexao.access_token); base = settings.instagram_graph_base_url.rstrip("/"); versao = settings.instagram_api_version or settings.meta_api_version
    if not token: raise RuntimeError("Token do Instagram ausente")
    async with httpx.AsyncClient(timeout=90) as client:
        urls = [await _url_item(item) for item in itens]
        if publicacao.formato == "reels":
            r = await client.post(f"{base}/{versao}/{conexao.external_id}/media", params={"media_type": "REELS", "video_url": urls[0], "caption": _legenda(publicacao), "access_token": token})
        elif publicacao.formato == "carrossel":
            ids = []
            for url in urls:
                r = await client.post(f"{base}/{versao}/{conexao.external_id}/media", params={"image_url": url, "is_carousel_item": "true", "access_token": token}); r.raise_for_status(); ids.append(r.json()["id"])
            r = await client.post(f"{base}/{versao}/{conexao.external_id}/media", params={"media_type": "CAROUSEL", "children": ",".join(ids), "caption": _legenda(publicacao), "access_token": token})
        else:
            r = await client.post(f"{base}/{versao}/{conexao.external_id}/media", params={"image_url": urls[0], "caption": _legenda(publicacao), "access_token": token})
        if r.status_code >= 400: raise RuntimeError(_erro_api(r))
        creation = r.json().get("id")
        publicar = await client.post(f"{base}/{versao}/{conexao.external_id}/media_publish", params={"creation_id": creation, "access_token": token})
        if publicar.status_code >= 400: raise RuntimeError(_erro_api(publicar))
        return str(publicar.json().get("id", creation))


async def publicar_facebook(publicacao, itens, conexao):
    token = descriptografar(conexao.access_token); base = settings.facebook_graph_base_url.rstrip("/"); versao = settings.facebook_api_version or settings.meta_api_version
    if not token: raise RuntimeError("Token da Página do Facebook ausente")
    async with httpx.AsyncClient(timeout=90) as client:
        url = await _url_item(itens[0])
        if publicacao.formato == "reels":
            raise RuntimeError("A publicação de Reels no Facebook exige o fluxo de vídeo da Meta e ainda não está habilitada nesta conta")
        r = await client.post(f"{base}/{versao}/{conexao.external_id}/photos", params={"url": url, "caption": _legenda(publicacao), "access_token": token})
        if r.status_code >= 400: raise RuntimeError(_erro_api(r))
        return str(r.json().get("post_id") or r.json().get("id"))


async def publicar_linkedin(publicacao, itens, conexao):
    raise RuntimeError("Publicação no LinkedIn requer que o aplicativo tenha a permissão w_member_social aprovada e o fluxo de mídia registrado")


def _legenda(publicacao):
    return (publicacao.legenda.strip() + "\n\n" + " ".join(publicacao.hashtags)).strip()


def _erro_api(response):
    try: return response.json().get("error", {}).get("message", f"HTTP {response.status_code}")
    except Exception: return f"HTTP {response.status_code}"


@router.post("/{publicacao_id}/publicar")
async def publicar(publicacao_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    await publicar_por_id(publicacao_id, usuario_id, db)
    publicacao = db.scalar(select(Publicacao).where(Publicacao.id == publicacao_id, Publicacao.usuario_id == usuario_id))
    redes = db.scalars(select(PublicacaoRede).where(PublicacaoRede.publicacao_id == publicacao_id)).all()
    return _serializar(publicacao, redes)


@router.post("/{publicacao_id}/cancelar")
def cancelar(publicacao_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    item = db.scalar(select(Publicacao).where(Publicacao.id == publicacao_id, Publicacao.usuario_id == usuario_id))
    if not item: raise HTTPException(404, "Publicação não encontrada")
    if item.status == "publicada": raise HTTPException(409, "Publicação já realizada")
    item.status = "cancelada"; db.commit(); return {"id": str(item.id), "status": item.status}
