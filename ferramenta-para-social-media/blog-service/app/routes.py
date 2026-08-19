import hashlib
import json
import re
import httpx
from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.ai import ErroIA, gerar_artigo, gerar_ideias, gerar_imagem
from app.auth import obter_usuario_id
from app.crypto import criptografar
from app.database import get_db
from app.integrations import adicionar_ideia_planilha, listar_planilhas_google, normalizar_wordpress_url, publicar_wordpress, testar_wordpress
from app.models import ArtigoBlog, IdeiaBlog, IntegracaoBlog
from app.google_oauth import concluir_oauth, url_autorizacao
from app.config import settings

router = APIRouter()


class IntegracaoIn(BaseModel):
    wordpress_url: str | None = None
    wordpress_usuario: str | None = None
    wordpress_senha_app: str | None = None
    wordpress_status_padrao: str = "draft"
    google_planilha_id: str | None = None
    google_aba: str = "Ideias de Blog"
    google_conta_servico_json: str | None = None


class IdeiaIn(BaseModel):
    titulo: str = Field(min_length=3, max_length=500)
    tema: str = Field(min_length=3, max_length=500)
    palavra_chave: str = Field(min_length=2, max_length=250)
    palavras_secundarias: list[str] = []
    intencao_busca: str = "informacional"
    foco: str | None = None
    tamanho: str = "1500_2500"
    gerar_imagens: bool = True
    destino_wordpress: str = "nenhum"
    agendado_para: datetime | None = None
    salvar_google_sheets: bool = False


class GerarIdeiasIn(BaseModel):
    quantidade: int = Field(default=10, ge=1, le=50)
    instrucao: str = Field(default="", max_length=4000)
    tamanho: str = "1500_2500"
    gerar_imagens: bool = True
    salvar_google_sheets: bool = False


class PublicarIn(BaseModel):
    status: str = "draft"
    agendado_para: datetime | None = None


def validar_cliente(db, usuario_id, cliente_id):
    existe = db.scalar(text("SELECT EXISTS(SELECT 1 FROM social.clientes WHERE id=:c AND usuario_id=:u)"), {"c": cliente_id, "u": usuario_id})
    if not existe:
        raise HTTPException(404, "Cliente não encontrado")


def arsenal(db, usuario_id, cliente_id):
    row = db.execute(text("SELECT informacoes, manual_ia FROM content.arsenais_copy WHERE usuario_id=:u AND cliente_id=:c"), {"u": usuario_id, "c": cliente_id}).mappings().first()
    return (row["informacoes"] or {}, row["manual_ia"] or "") if row else ({}, "")


def fingerprint(cliente_id, titulo, chave):
    normal = re.sub(r"\W+", " ", f"{cliente_id} {titulo} {chave}".lower()).strip()
    return hashlib.sha256(normal.encode()).hexdigest()


def ideia_dict(i):
    return {c: getattr(i, c) for c in ("id", "cliente_id", "titulo", "tema", "palavra_chave", "palavras_secundarias", "intencao_busca", "foco", "tamanho", "gerar_imagens", "destino_wordpress", "status", "agendado_para", "origem", "google_linha", "erro", "processado_em", "criado_em")}


def artigo_dict(a, completo=True):
    data = {c: getattr(a, c) for c in ("id", "ideia_id", "cliente_id", "titulo", "meta_titulo", "meta_descricao", "slug", "resumo", "palavra_chave", "palavras_secundarias", "intencao_busca", "estrutura", "faq", "imagens", "checklist_seo", "pontuacao_seo", "total_palavras", "modelo_ia", "status", "agendado_para", "wordpress_post_id", "wordpress_url", "publicado_em", "criado_em", "atualizado_em")}
    if completo:
        data["conteudo_html"] = a.conteudo_html
    return data


def obter_integracao(db, usuario_id, cliente_id):
    return db.scalar(select(IntegracaoBlog).where(IntegracaoBlog.usuario_id == usuario_id, IntegracaoBlog.cliente_id == cliente_id))


@router.get("/integracoes/{cliente_id}")
def ver_integracao(cliente_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    validar_cliente(db, usuario_id, cliente_id); i = obter_integracao(db, usuario_id, cliente_id)
    central = db.execute(text("SELECT email FROM social.google_conexoes WHERE usuario_id=:u AND cliente_id=:c"),{"u":usuario_id,"c":cliente_id}).first()
    if not i:
        return {"cliente_id": cliente_id, "wordpress_configurado": False, "google_configurado": bool(central), "google_email": central[0] if central else None, "google_modo": "central" if central else None, "wordpress_status_padrao": "draft", "google_aba": "Ideias de Blog"}
    return {"cliente_id": cliente_id, "wordpress_url": i.wordpress_url, "wordpress_usuario": i.wordpress_usuario,
            "wordpress_status_padrao": i.wordpress_status_padrao, "wordpress_configurado": bool(i.wordpress_senha_app),
            "google_planilha_id": i.google_planilha_id, "google_aba": i.google_aba,
            "google_email": central[0] if central else i.google_email, "google_modo": "central" if central else ("oauth" if i.google_refresh_token else "conta_servico"),
            "google_configurado": bool(central or i.google_refresh_token or i.google_conta_servico)}


@router.put("/integracoes/{cliente_id}")
def salvar_integracao(cliente_id: UUID, dados: IntegracaoIn, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    validar_cliente(db, usuario_id, cliente_id)
    if dados.wordpress_status_padrao not in {"draft", "publish", "future"}:
        raise HTTPException(422, "Status WordPress inválido")
    i = obter_integracao(db, usuario_id, cliente_id) or IntegracaoBlog(usuario_id=usuario_id, cliente_id=cliente_id)
    if dados.wordpress_url:
        try: i.wordpress_url = normalizar_wordpress_url(dados.wordpress_url)
        except ValueError as erro: raise HTTPException(422, str(erro))
    else: i.wordpress_url = None
    i.wordpress_usuario = dados.wordpress_usuario or None
    i.wordpress_status_padrao = dados.wordpress_status_padrao
    planilha = (dados.google_planilha_id or "").strip()
    if "/spreadsheets/d/" in planilha:
        planilha = planilha.split("/spreadsheets/d/", 1)[1].split("/", 1)[0]
    if planilha and not re.fullmatch(r"[A-Za-z0-9_-]+", planilha):
        raise HTTPException(422, "ID da planilha Google inválido")
    i.google_planilha_id = planilha or None; i.google_aba = "Ideias de Blog"
    if dados.wordpress_senha_app: i.wordpress_senha_app = criptografar(dados.wordpress_senha_app.replace(" ", ""))
    if dados.google_conta_servico_json:
        try: json.loads(dados.google_conta_servico_json)
        except ValueError: raise HTTPException(422, "JSON da conta de serviço Google inválido")
        i.google_conta_servico = criptografar(dados.google_conta_servico_json)
    db.add(i); db.commit()
    return ver_integracao(cliente_id, usuario_id, db)


@router.post("/integracoes/{cliente_id}/testar-wordpress")
async def teste_wp(cliente_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    i = obter_integracao(db, usuario_id, cliente_id)
    if not i: raise HTTPException(400, "Configure o WordPress primeiro")
    try: return await testar_wordpress(i)
    except Exception as erro: raise HTTPException(502, f"Falha no WordPress: {erro}")

@router.get("/oauth/google/iniciar/{cliente_id}")
def iniciar_google(cliente_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    validar_cliente(db, usuario_id, cliente_id)
    try: return {"url": url_autorizacao(usuario_id, cliente_id)}
    except ValueError as erro: raise HTTPException(503, str(erro))

@router.get("/oauth/google/callback")
async def callback_google(code: str | None = None, state: str | None = None, error: str | None = None, db: Session = Depends(get_db)):
    destino = (settings.frontend_url or "").rstrip("/") + "/blog"
    if error or not code or not state: return RedirectResponse(f"{destino}?sheets=cancelado")
    try: await concluir_oauth(db, code, state)
    except ValueError: return RedirectResponse(f"{destino}?sheets=erro")
    return RedirectResponse(f"{destino}?sheets=conectado")

@router.delete("/oauth/google/{cliente_id}", status_code=204)
def desconectar_google(cliente_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    i = obter_integracao(db, usuario_id, cliente_id)
    if i:
        i.google_email = None; i.google_access_token = None; i.google_refresh_token = None; i.google_token_expira_em = None; db.commit()

@router.get("/integracoes/{cliente_id}/planilhas-google")
async def listar_planilhas(cliente_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    validar_cliente(db, usuario_id, cliente_id); i = obter_integracao(db, usuario_id, cliente_id)
    if not i: raise HTTPException(400, "Conecte a conta Google deste cliente")
    try: return await listar_planilhas_google(i, db)
    except ValueError as erro: raise HTTPException(403, str(erro))
    except httpx.HTTPError as erro: raise HTTPException(502, f"Google Drive recusou a consulta: {erro}")


async def enviar_sheets_se_pedido(db, ideia, pedido):
    if not pedido: return
    i = obter_integracao(db, ideia.usuario_id, ideia.cliente_id)
    central=db.execute(text("SELECT 1 FROM social.google_conexoes WHERE usuario_id=:u AND cliente_id=:c"),{"u":ideia.usuario_id,"c":ideia.cliente_id}).first()
    if not i or not (central or i.google_refresh_token or i.google_conta_servico) or not i.google_planilha_id:
        raise HTTPException(400, "Configure a integração Google Sheets deste cliente")
    try: ideia.google_linha = await adicionar_ideia_planilha(i, ideia, db); db.commit()
    except Exception as erro: raise HTTPException(502, f"Ideia criada, mas não foi enviada ao Google Sheets: {erro}")


@router.post("/clientes/{cliente_id}/ideias")
async def criar_ideia(cliente_id: UUID, dados: IdeiaIn, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    validar_cliente(db, usuario_id, cliente_id)
    if dados.destino_wordpress not in {"nenhum", "draft", "publish"}: raise HTTPException(422, "Destino WordPress inválido")
    status = "agendada" if dados.agendado_para else "ideia"
    i = IdeiaBlog(usuario_id=usuario_id, cliente_id=cliente_id, status=status, origem="manual",
                  fingerprint=fingerprint(cliente_id, dados.titulo, dados.palavra_chave), **dados.model_dump(exclude={"salvar_google_sheets"}))
    db.add(i)
    try: db.commit(); db.refresh(i)
    except IntegrityError: db.rollback(); raise HTTPException(409, "Esta ideia já existe para o cliente")
    await enviar_sheets_se_pedido(db, i, dados.salvar_google_sheets)
    return ideia_dict(i)


@router.post("/clientes/{cliente_id}/ideias/gerar")
async def gerar_lista(cliente_id: UUID, dados: GerarIdeiasIn, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    validar_cliente(db, usuario_id, cliente_id); info, manual = arsenal(db, usuario_id, cliente_id)
    try: _, lista = await gerar_ideias(info, manual, dados.quantidade, dados.instrucao)
    except ErroIA as erro: raise HTTPException(502, str(erro))
    saida = []
    for item in lista:
        if not item.get("titulo") or not item.get("palavra_chave"): continue
        i = IdeiaBlog(usuario_id=usuario_id, cliente_id=cliente_id, titulo=item["titulo"][:500], tema=(item.get("tema") or item["titulo"])[:500], palavra_chave=item["palavra_chave"][:250], palavras_secundarias=item.get("palavras_secundarias", []), intencao_busca=item.get("intencao_busca", "informacional"), foco=item.get("foco"), tamanho=dados.tamanho, gerar_imagens=dados.gerar_imagens, status="ideia", origem="ia", fingerprint=fingerprint(cliente_id, item["titulo"], item["palavra_chave"]))
        db.add(i)
        try: db.commit(); db.refresh(i)
        except IntegrityError: db.rollback(); continue
        await enviar_sheets_se_pedido(db, i, dados.salvar_google_sheets); saida.append(ideia_dict(i))
    return saida


@router.get("/clientes/{cliente_id}/ideias")
def listar_ideias(cliente_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    validar_cliente(db, usuario_id, cliente_id)
    return [ideia_dict(i) for i in db.scalars(select(IdeiaBlog).where(IdeiaBlog.usuario_id == usuario_id, IdeiaBlog.cliente_id == cliente_id).order_by(IdeiaBlog.criado_em.desc())).all()]


async def processar_ideia(db, ideia):
    existente = db.scalar(select(ArtigoBlog).where(ArtigoBlog.ideia_id == ideia.id))
    if existente: return existente
    info, manual = arsenal(db, ideia.usuario_id, ideia.cliente_id)
    modelo, data = await gerar_artigo(ideia, info, manual)
    imagens = []
    if ideia.gerar_imagens:
        for prompt in data.get("prompts_imagens", [])[:4]:
            try:
                arquivo = await gerar_imagem(prompt.get("prompt", "")); imagens.append({**prompt, **(arquivo or {})})
            except Exception as erro: imagens.append({**prompt, "erro": str(erro)})
    artigo = ArtigoBlog(ideia_id=ideia.id, usuario_id=ideia.usuario_id, cliente_id=ideia.cliente_id,
        titulo=data.get("titulo", ideia.titulo)[:500], meta_titulo=data.get("meta_titulo", ideia.titulo)[:200], meta_descricao=data.get("meta_descricao", "")[:400], slug=data.get("slug", "")[:500], resumo=data.get("resumo", ""), palavra_chave=ideia.palavra_chave, palavras_secundarias=data.get("palavras_secundarias", ideia.palavras_secundarias), intencao_busca=ideia.intencao_busca, conteudo_html=data.get("conteudo_html", ""), estrutura=data.get("estrutura", []), faq=data.get("faq", []), imagens=imagens, checklist_seo=data.get("checklist_seo", {}), pontuacao_seo=int(data.get("pontuacao_seo", 0)), total_palavras=int(data.get("total_palavras", 0)), modelo_ia=modelo, status="gerado", agendado_para=ideia.agendado_para)
    ideia.status = "artigo_pronto"; ideia.processado_em = datetime.now(timezone.utc); ideia.erro = None
    db.add(artigo); db.commit(); db.refresh(artigo); return artigo


@router.post("/ideias/{ideia_id}/gerar-artigo")
async def gerar_da_ideia(ideia_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    i = db.scalar(select(IdeiaBlog).where(IdeiaBlog.id == ideia_id, IdeiaBlog.usuario_id == usuario_id))
    if not i: raise HTTPException(404, "Ideia não encontrada")
    try: return artigo_dict(await processar_ideia(db, i))
    except ErroIA as erro: i.status = "erro"; i.erro = str(erro); db.commit(); raise HTTPException(502, str(erro))


@router.get("/clientes/{cliente_id}/artigos")
def listar_artigos(cliente_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    validar_cliente(db, usuario_id, cliente_id)
    return [artigo_dict(a, False) for a in db.scalars(select(ArtigoBlog).where(ArtigoBlog.usuario_id == usuario_id, ArtigoBlog.cliente_id == cliente_id).order_by(ArtigoBlog.criado_em.desc())).all()]


@router.get("/artigos/{artigo_id}")
def ver_artigo(artigo_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    a = db.scalar(select(ArtigoBlog).where(ArtigoBlog.id == artigo_id, ArtigoBlog.usuario_id == usuario_id))
    if not a: raise HTTPException(404, "Artigo não encontrado")
    return artigo_dict(a)


@router.put("/artigos/{artigo_id}")
def editar_artigo(artigo_id: UUID, dados: dict, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    a = db.scalar(select(ArtigoBlog).where(ArtigoBlog.id == artigo_id, ArtigoBlog.usuario_id == usuario_id))
    if not a: raise HTTPException(404, "Artigo não encontrado")
    for campo in ("titulo", "meta_titulo", "meta_descricao", "slug", "resumo", "conteudo_html"):
        if campo in dados and isinstance(dados[campo], str): setattr(a, campo, dados[campo])
    db.commit(); db.refresh(a); return artigo_dict(a)


@router.post("/artigos/{artigo_id}/wordpress")
async def enviar_wordpress(artigo_id: UUID, dados: PublicarIn, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    if dados.status not in {"draft", "publish", "future"}: raise HTTPException(422, "Status inválido")
    if dados.status == "future" and not dados.agendado_para: raise HTTPException(422, "Informe a data do agendamento")
    a = db.scalar(select(ArtigoBlog).where(ArtigoBlog.id == artigo_id, ArtigoBlog.usuario_id == usuario_id))
    if not a: raise HTTPException(404, "Artigo não encontrado")
    i = obter_integracao(db, usuario_id, a.cliente_id)
    if not i: raise HTTPException(400, "Configure o WordPress deste cliente")
    try: post_id, url = await publicar_wordpress(i, a, dados.status, dados.agendado_para)
    except Exception as erro: raise HTTPException(502, f"Falha ao enviar ao WordPress: {erro}")
    a.wordpress_post_id = post_id; a.wordpress_url = url; a.status = {"draft":"rascunho_wordpress", "future":"agendado_wordpress", "publish":"publicado"}[dados.status]
    a.agendado_para = dados.agendado_para; a.publicado_em = datetime.now(timezone.utc) if dados.status == "publish" else None
    db.commit(); db.refresh(a); return artigo_dict(a)


@router.delete("/ideias/{ideia_id}", status_code=204)
def excluir_ideia(ideia_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    i = db.scalar(select(IdeiaBlog).where(IdeiaBlog.id == ideia_id, IdeiaBlog.usuario_id == usuario_id))
    if not i: raise HTTPException(404, "Ideia não encontrada")
    db.delete(i); db.commit(); return Response(status_code=204)


@router.delete("/artigos/{artigo_id}", status_code=204)
def excluir_artigo(artigo_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    a = db.scalar(select(ArtigoBlog).where(ArtigoBlog.id == artigo_id, ArtigoBlog.usuario_id == usuario_id))
    if not a: raise HTTPException(404, "Artigo não encontrado")
    db.delete(a); db.commit(); return Response(status_code=204)
