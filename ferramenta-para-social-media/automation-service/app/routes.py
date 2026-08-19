import asyncio
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from app.auth import obter_usuario_id
from app.database import get_db
from app.models import AutomationFlow, AutomationSettings, Contact, CrmActivity
from app.google_calendar import atualizar_evento, criar_evento, excluir_evento, listar_eventos, requisicao
from app.google_oauth import concluir_oauth, url_autorizacao
from app.config import settings
from app.integrations import (
    IntegrationError,
    evolution,
    evolution_configurada,
    n8n,
    n8n_configurado,
    validar_typebot_publico,
)

router = APIRouter()

class FluxoEntrada(BaseModel):
    cliente_id: UUID
    canal: str = Field(pattern="^(facebook|instagram)$")
    nome: str = Field(min_length=2, max_length=255)
    status: str = Field(default="rascunho", pattern="^(rascunho|ativo|pausado)$")
    blocos: list = Field(default_factory=list)
    conexoes: list = Field(default_factory=list)
    proximo_numero: int = Field(default=1, ge=1)

class CoresEntrada(BaseModel):
    cores: dict[str, str]

class ContatoEntrada(BaseModel):
    cliente_id: UUID
    canal: str = "manual"
    external_id: str | None = None
    nome: str = Field(min_length=1, max_length=255)
    sobrenome: str = ""
    telefone: str | None = None
    email: str | None = None
    instagram_usuario: str | None = None
    facebook_usuario: str | None = None
    etapa_id: str | None = None
    qualidade_id: str | None = None
    tags: list[str] = Field(default_factory=list)
    respostas: list = Field(default_factory=list)

class CrmConfigEntrada(BaseModel):
    etapas: list[dict] = Field(default_factory=list)
    tags: list[dict] = Field(default_factory=list)
    qualidades: list[dict] = Field(default_factory=list)

class AtividadeEntrada(BaseModel):
    cliente_id: UUID
    contato_id: UUID | None = None
    tipo: str = Field(pattern="^(agendamento|tarefa|recado|compromisso)$")
    titulo: str = Field(min_length=1, max_length=255)
    descricao: str = ""
    inicio_em: datetime
    fim_em: datetime | None = None
    concluida: bool = False
    convidados: list[str] = Field(default_factory=list)

class GoogleCalendarEntrada(BaseModel):
    calendar_id: str = Field(min_length=3, max_length=320)

class TypebotEntrada(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    url_publica: str = Field(min_length=10, max_length=500)

class N8nVinculosEntrada(BaseModel):
    workflow_ids: list[str] = Field(default_factory=list, max_length=200)

CORES_PADRAO = {"mensagem": "#4f46e5", "pergunta": "#0891b2", "botoes": "#db2777", "espera": "#64748b", "decisao": "#d97706", "randomizacao": "#7c3aed", "gatilho": "#059669"}
CRM_PADRAO = {
    "etapas": [
        {"id": "novo", "nome": "Novo lead", "cor_fundo": "#dbeafe", "cor_texto": "#1e40af"},
        {"id": "contato", "nome": "Em contato", "cor_fundo": "#fef3c7", "cor_texto": "#92400e"},
        {"id": "proposta", "nome": "Proposta", "cor_fundo": "#ede9fe", "cor_texto": "#5b21b6"},
        {"id": "cliente", "nome": "Cliente", "cor_fundo": "#dcfce7", "cor_texto": "#166534"},
    ],
    "tags": [],
    "qualidades": [
        {"id": "frio", "nome": "Frio", "cor_fundo": "#e2e8f0", "cor_texto": "#334155"},
        {"id": "morno", "nome": "Morno", "cor_fundo": "#fef3c7", "cor_texto": "#92400e"},
        {"id": "quente", "nome": "Quente", "cor_fundo": "#fee2e2", "cor_texto": "#991b1b"},
    ],
}

def serializar_contato(item):
    return {"id": str(item.id), "cliente_id": str(item.cliente_id), "canal": item.canal,
            "external_id": item.external_id, "nome": item.nome, "sobrenome": item.sobrenome,
            "telefone": item.telefone, "email": item.email, "instagram_usuario": item.instagram_usuario,
            "facebook_usuario": item.facebook_usuario, "etapa_id": item.etapa_id,
            "qualidade_id": item.qualidade_id, "tags": item.tags or [], "respostas": item.respostas or [],
            "atualizado_em": item.atualizado_em}

def obter_settings(db, usuario_id, cliente_id, criar=False):
    item = db.scalar(select(AutomationSettings).where(AutomationSettings.usuario_id == usuario_id, AutomationSettings.cliente_id == cliente_id))
    if not item and criar:
        item = AutomationSettings(usuario_id=usuario_id, cliente_id=cliente_id, cores={}, crm_config={}); db.add(item)
    return item

def serializar_fluxo(item):
    return {"id": str(item.id), "cliente_id": str(item.cliente_id), "canal": item.canal, "nome": item.nome,
            "status": item.status, "blocos": item.blocos, "conexoes": item.conexoes,
            "proximo_numero": item.proximo_numero, "atualizado_em": item.atualizado_em}

@router.get("/fluxos")
def listar_fluxos(cliente_id: UUID | None = None, canal: str | None = None, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    consulta = select(AutomationFlow).where(AutomationFlow.usuario_id == usuario_id)
    if cliente_id: consulta = consulta.where(AutomationFlow.cliente_id == cliente_id)
    if canal: consulta = consulta.where(AutomationFlow.canal == canal)
    return [serializar_fluxo(item) for item in db.scalars(consulta.order_by(AutomationFlow.atualizado_em.desc())).all()]

@router.post("/fluxos", status_code=201)
def criar_fluxo(dados: FluxoEntrada, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    item = AutomationFlow(usuario_id=usuario_id, **dados.model_dump()); db.add(item); db.commit(); db.refresh(item)
    return serializar_fluxo(item)

@router.put("/fluxos/{fluxo_id}")
def salvar_fluxo(fluxo_id: UUID, dados: FluxoEntrada, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    item = db.scalar(select(AutomationFlow).where(AutomationFlow.id == fluxo_id, AutomationFlow.usuario_id == usuario_id))
    if not item: raise HTTPException(status_code=404, detail="Automação não encontrada")
    for chave, valor in dados.model_dump().items(): setattr(item, chave, valor)
    db.commit(); db.refresh(item); return serializar_fluxo(item)

@router.delete("/fluxos/{fluxo_id}", status_code=204)
def excluir_fluxo(fluxo_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    item = db.scalar(select(AutomationFlow).where(AutomationFlow.id == fluxo_id, AutomationFlow.usuario_id == usuario_id))
    if not item: raise HTTPException(status_code=404, detail="Automação não encontrada")
    db.delete(item); db.commit()

@router.get("/contatos")
def listar_contatos(cliente_id: UUID | None = None, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    consulta = select(Contact).where(Contact.usuario_id == usuario_id)
    if cliente_id: consulta = consulta.where(Contact.cliente_id == cliente_id)
    itens = db.scalars(consulta.order_by(Contact.atualizado_em.desc())).all()
    return [serializar_contato(item) for item in itens]

@router.post("/contatos", status_code=201)
def criar_contato(dados: ContatoEntrada, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    valores = dados.model_dump(); valores["external_id"] = valores["external_id"] or f"manual-{uuid4()}"
    item = Contact(usuario_id=usuario_id, **valores); db.add(item); db.commit(); db.refresh(item)
    return serializar_contato(item)

@router.put("/contatos/{contato_id}")
def atualizar_contato(contato_id: UUID, dados: ContatoEntrada, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    item = db.scalar(select(Contact).where(Contact.id == contato_id, Contact.usuario_id == usuario_id))
    if not item: raise HTTPException(status_code=404, detail="Lead não encontrado")
    for chave, valor in dados.model_dump(exclude={"external_id"}).items(): setattr(item, chave, valor)
    if dados.external_id: item.external_id = dados.external_id
    db.commit(); db.refresh(item); return serializar_contato(item)

@router.delete("/contatos/{contato_id}", status_code=204)
def excluir_contato(contato_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    item = db.scalar(select(Contact).where(Contact.id == contato_id, Contact.usuario_id == usuario_id))
    if not item: raise HTTPException(status_code=404, detail="Lead não encontrado")
    db.delete(item); db.commit()

@router.get("/crm/configuracoes/{cliente_id}")
def obter_crm_config(cliente_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    item = obter_settings(db, usuario_id, cliente_id)
    salvo = item.crm_config if item else {}
    return {chave: salvo.get(chave, valor) for chave, valor in CRM_PADRAO.items()}

@router.put("/crm/configuracoes/{cliente_id}")
def salvar_crm_config(cliente_id: UUID, dados: CrmConfigEntrada, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    item = obter_settings(db, usuario_id, cliente_id, True); item.crm_config = dados.model_dump(); db.commit()
    return item.crm_config

def serializar_atividade(item):
    return {"id": str(item.id), "cliente_id": str(item.cliente_id), "contato_id": str(item.contato_id) if item.contato_id else None,
            "tipo": item.tipo, "titulo": item.titulo, "descricao": item.descricao,
            "inicio_em": item.inicio_em, "fim_em": item.fim_em, "concluida": item.concluida,
            "google_event_id": item.google_event_id, "convidados": item.convidados or [], "origem": "plataforma"}

@router.get("/crm/atividades")
async def listar_atividades(cliente_id: UUID | None = None, inicio: datetime | None = None, fim: datetime | None = None, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    consulta = select(CrmActivity).where(CrmActivity.usuario_id == usuario_id)
    if cliente_id: consulta = consulta.where(CrmActivity.cliente_id == cliente_id)
    if inicio: consulta = consulta.where(CrmActivity.inicio_em >= inicio)
    if fim: consulta = consulta.where(CrmActivity.inicio_em < fim)
    internos = db.scalars(consulta.order_by(CrmActivity.inicio_em)).all()
    resultado = [serializar_atividade(x) for x in internos]
    if cliente_id:
        config = obter_settings(db, usuario_id, cliente_id)
        central=db.execute(text("SELECT 1 FROM social.google_conexoes WHERE usuario_id=:u AND cliente_id=:c"),{"u":usuario_id,"c":cliente_id}).first()
        if central or (config and config.google_calendar_id):
            inicio = inicio or datetime.now(timezone.utc) - timedelta(days=31)
            fim = fim or datetime.now(timezone.utc) + timedelta(days=62)
            try:
                externos = await listar_eventos(db, usuario_id, cliente_id, config.google_calendar_id if config else "primary", inicio, fim)
                ids_internos = {str(x.id) for x in internos}
                for evento in externos:
                    atividade_id = evento.get("extendedProperties", {}).get("private", {}).get("atividade_id")
                    if atividade_id in ids_internos: continue
                    comeco = evento.get("start", {}).get("dateTime") or evento.get("start", {}).get("date")
                    termino = evento.get("end", {}).get("dateTime") or evento.get("end", {}).get("date")
                    resultado.append({"id": f"google-{evento['id']}", "cliente_id": str(cliente_id), "contato_id": None,
                        "tipo": "compromisso", "titulo": evento.get("summary") or "Compromisso",
                        "descricao": evento.get("description") or "", "inicio_em": comeco, "fim_em": termino,
                        "concluida": False, "google_event_id": evento["id"],
                        "convidados": [x.get("email") for x in evento.get("attendees", []) if x.get("email")], "origem": "google"})
            except ValueError as erro:
                raise HTTPException(status_code=502, detail=f"Google Agenda: {erro}")
    return sorted(resultado, key=lambda x: str(x["inicio_em"]))

@router.post("/crm/atividades", status_code=201)
async def criar_atividade(dados: AtividadeEntrada, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    valores = dados.model_dump(); valores["fim_em"] = valores["fim_em"] or (valores["inicio_em"] + timedelta(hours=1))
    item = CrmActivity(usuario_id=usuario_id, **valores); db.add(item); db.flush()
    config = obter_settings(db, usuario_id, dados.cliente_id)
    central=db.execute(text("SELECT 1 FROM social.google_conexoes WHERE usuario_id=:u AND cliente_id=:c"),{"u":usuario_id,"c":dados.cliente_id}).first()
    if central or (config and config.google_calendar_id):
        try: item.google_event_id = (await criar_evento(db, usuario_id, item, config.google_calendar_id if config else "primary"))["id"]
        except ValueError as erro: db.rollback(); raise HTTPException(status_code=502, detail=f"Google Agenda: {erro}")
    db.commit(); db.refresh(item); return serializar_atividade(item)

@router.put("/crm/atividades/{atividade_id}")
async def salvar_atividade(atividade_id: UUID, dados: AtividadeEntrada, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    item = db.scalar(select(CrmActivity).where(CrmActivity.id == atividade_id, CrmActivity.usuario_id == usuario_id))
    if not item: raise HTTPException(status_code=404, detail="Atividade não encontrada")
    for chave, valor in dados.model_dump().items(): setattr(item, chave, valor)
    if not item.fim_em: item.fim_em = item.inicio_em + timedelta(hours=1)
    config = obter_settings(db, usuario_id, dados.cliente_id)
    central=db.execute(text("SELECT 1 FROM social.google_conexoes WHERE usuario_id=:u AND cliente_id=:c"),{"u":usuario_id,"c":dados.cliente_id}).first()
    if central or (config and config.google_calendar_id):
        try:
            calendar_id=config.google_calendar_id if config else "primary"
            if item.google_event_id: await atualizar_evento(db, usuario_id, item, calendar_id)
            else: item.google_event_id = (await criar_evento(db, usuario_id, item, calendar_id))["id"]
        except ValueError as erro: db.rollback(); raise HTTPException(status_code=502, detail=f"Google Agenda: {erro}")
    db.commit(); db.refresh(item); return serializar_atividade(item)

@router.delete("/crm/atividades/{atividade_id}", status_code=204)
async def excluir_atividade(atividade_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    item = db.scalar(select(CrmActivity).where(CrmActivity.id == atividade_id, CrmActivity.usuario_id == usuario_id))
    if not item: raise HTTPException(status_code=404, detail="Atividade não encontrada")
    config = obter_settings(db, usuario_id, item.cliente_id)
    central=db.execute(text("SELECT 1 FROM social.google_conexoes WHERE usuario_id=:u AND cliente_id=:c"),{"u":usuario_id,"c":item.cliente_id}).first()
    if central or (config and config.google_calendar_id):
        try: await excluir_evento(db, usuario_id, item, config.google_calendar_id if config else "primary")
        except ValueError as erro: raise HTTPException(status_code=502, detail=f"Google Agenda: {erro}")
    db.delete(item); db.commit()

@router.get("/crm/calendario/integracao/{cliente_id}")
def obter_integracao_calendario(cliente_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    item = obter_settings(db, usuario_id, cliente_id)
    return {"cliente_id": str(cliente_id), "calendar_id": item.google_calendar_id if item else "",
            "google_email": item.google_email if item else "", "modo": "oauth" if item and item.google_refresh_token else "conta_servico",
            "configurado": bool(item and item.google_calendar_id)}

@router.get("/oauth/google/iniciar/{cliente_id}")
def iniciar_google_oauth(cliente_id: UUID, usuario_id: UUID = Depends(obter_usuario_id)):
    try: return {"url": url_autorizacao(usuario_id, cliente_id)}
    except ValueError as erro: raise HTTPException(status_code=503, detail=str(erro))

@router.get("/oauth/google/callback")
async def callback_google_oauth(code: str | None = None, state: str | None = None, error: str | None = None, db: Session = Depends(get_db)):
    destino = (settings.frontend_url or "").rstrip("/") + "/crm/calendario"
    if error or not code or not state: return RedirectResponse(f"{destino}?google=cancelado")
    try: await concluir_oauth(db, code, state)
    except ValueError: return RedirectResponse(f"{destino}?google=erro")
    return RedirectResponse(f"{destino}?google=conectado")

@router.delete("/oauth/google/{cliente_id}", status_code=204)
def desconectar_google_oauth(cliente_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    item = obter_settings(db, usuario_id, cliente_id)
    if item:
        item.google_access_token = None; item.google_refresh_token = None; item.google_token_expira_em = None
        item.google_email = None; item.google_calendar_id = None; db.commit()

@router.put("/crm/calendario/integracao/{cliente_id}")
async def salvar_integracao_calendario(cliente_id: UUID, dados: GoogleCalendarEntrada, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    item = obter_settings(db, usuario_id, cliente_id, True); calendar_id = dados.calendar_id.strip()
    try: await requisicao(db, usuario_id, cliente_id, calendar_id, "GET")
    except ValueError as erro: raise HTTPException(status_code=502, detail=f"Google Agenda: {erro}")
    item.google_calendar_id = calendar_id; db.commit()
    return {"cliente_id": str(cliente_id), "calendar_id": calendar_id, "configurado": True}

@router.get("/configuracoes/{cliente_id}")
def obter_configuracoes(cliente_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    item = db.scalar(select(AutomationSettings).where(AutomationSettings.usuario_id == usuario_id, AutomationSettings.cliente_id == cliente_id))
    return {"cliente_id": str(cliente_id), "cores": {**CORES_PADRAO, **(item.cores if item else {})}}

@router.put("/configuracoes/{cliente_id}")
def salvar_configuracoes(cliente_id: UUID, dados: CoresEntrada, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    item = db.scalar(select(AutomationSettings).where(AutomationSettings.usuario_id == usuario_id, AutomationSettings.cliente_id == cliente_id))
    if not item:
        item = AutomationSettings(usuario_id=usuario_id, cliente_id=cliente_id, cores={}); db.add(item)
    item.cores = {**CORES_PADRAO, **dados.cores}; db.commit()
    return {"cliente_id": str(cliente_id), "cores": item.cores}


def _integracoes(item):
    return dict(item.integracoes or {}) if item else {}


@router.get("/integracoes/{cliente_id}")
def obter_integracoes(cliente_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    item = obter_settings(db, usuario_id, cliente_id)
    salvo = _integracoes(item)
    return {
        "cliente_id": str(cliente_id),
        "evolution": {"configurada": evolution_configurada(), "instancia": salvo.get("evolution_instance")},
        "n8n": {"configurado": n8n_configurado(), "workflow_ids": salvo.get("n8n_workflow_ids", [])},
        "typebot": {
            "configurado": bool(settings.typebot_viewer_url),
            "viewer_url": settings.normalizar_url(settings.typebot_viewer_url),
            "builder_url": settings.normalizar_url(settings.typebot_builder_url),
            "bots": salvo.get("typebots", []),
        },
    }


@router.put("/integracoes/{cliente_id}/typebots")
def salvar_typebots(cliente_id: UUID, dados: list[TypebotEntrada], usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    item = obter_settings(db, usuario_id, cliente_id, True)
    integracoes = _integracoes(item)
    integracoes["typebots"] = [
        {"id": str(uuid4()), "nome": bot.nome.strip(), "url_publica": validar_typebot_publico(bot.url_publica)}
        for bot in dados
    ]
    item.integracoes = integracoes
    db.commit()
    return integracoes["typebots"]


@router.get("/integracoes/{cliente_id}/whatsapp")
async def obter_whatsapp(cliente_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    item = obter_settings(db, usuario_id, cliente_id)
    instancia = _integracoes(item).get("evolution_instance")
    if not instancia:
        return {"configurada": evolution_configurada(), "instancia": None, "estado": "nao_criada"}
    try:
        resposta = await evolution("GET", f"instance/connectionState/{instancia}")
    except IntegrationError as erro:
        return {"configurada": evolution_configurada(), "instancia": instancia, "estado": "indisponivel", "erro": str(erro)}
    estado = (resposta or {}).get("instance", {}).get("state") or (resposta or {}).get("state") or "desconhecido"
    return {"configurada": True, "instancia": instancia, "estado": estado}


@router.post("/integracoes/{cliente_id}/whatsapp", status_code=201)
async def criar_whatsapp(cliente_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    item = obter_settings(db, usuario_id, cliente_id, True)
    integracoes = _integracoes(item)
    instancia = integracoes.get("evolution_instance") or f"sm_{cliente_id.hex}"
    try:
        try:
            resposta = await evolution("POST", "instance/create", payload={
                "instanceName": instancia,
                "qrcode": True,
                "integration": settings.evolution_integration,
            })
        except IntegrationError as erro:
            if erro.status_code not in {400, 409}:
                raise
            resposta = {"instance": {"instanceName": instancia}, "reutilizada": True}
        if settings.evolution_webhook_url:
            await evolution("POST", f"webhook/set/{instancia}", payload={
                "webhook": {
                    "enabled": True,
                    "url": settings.evolution_webhook_url,
                    "byEvents": False,
                    "base64": False,
                    "events": ["MESSAGES_UPSERT", "CONNECTION_UPDATE"],
                }
            })
    except IntegrationError as erro:
        raise HTTPException(status_code=502, detail=f"Evolution API: {erro}")
    integracoes["evolution_instance"] = instancia
    item.integracoes = integracoes
    db.commit()
    return {"instancia": instancia, "dados": resposta}


@router.get("/integracoes/{cliente_id}/whatsapp/qrcode")
async def obter_qrcode_whatsapp(cliente_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    item = obter_settings(db, usuario_id, cliente_id)
    instancia = _integracoes(item).get("evolution_instance")
    if not instancia:
        raise HTTPException(status_code=404, detail="Crie a conexão do WhatsApp primeiro.")
    try:
        ultima = None
        for tentativa in range(4):
            try:
                resposta = await evolution("GET", f"instance/connect/{instancia}")
                if resposta and any(resposta.get(chave) or resposta.get("data", {}).get(chave) for chave in ("base64", "code", "pairingCode")):
                    return resposta
                ultima = resposta
            except IntegrationError as erro:
                ultima = erro
            if tentativa < 3:
                await asyncio.sleep(1.5)
        if isinstance(ultima, IntegrationError):
            raise ultima
        return ultima or {"instance": {"instanceName": instancia}, "message": "QR Code ainda não disponível"}
    except IntegrationError as erro:
        codigo = 502 if erro.status_code is None else erro.status_code
        raise HTTPException(status_code=codigo, detail=f"Evolution API: {erro}")


@router.delete("/integracoes/{cliente_id}/whatsapp", status_code=204)
async def excluir_whatsapp(cliente_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    item = obter_settings(db, usuario_id, cliente_id)
    integracoes = _integracoes(item)
    instancia = integracoes.get("evolution_instance")
    if not instancia:
        return
    try:
        await evolution("DELETE", f"instance/delete/{instancia}")
    except IntegrationError as erro:
        raise HTTPException(status_code=502, detail=f"Evolution API: {erro}")
    integracoes.pop("evolution_instance", None)
    item.integracoes = integracoes
    db.commit()


@router.get("/integracoes/{cliente_id}/n8n/workflows")
async def listar_n8n_workflows(cliente_id: UUID, todos: bool = False, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    item = obter_settings(db, usuario_id, cliente_id)
    vinculados = set(_integracoes(item).get("n8n_workflow_ids", []))
    try:
        resposta = await n8n("GET", "workflows", params={"limit": 100})
    except IntegrationError as erro:
        raise HTTPException(status_code=502, detail=f"n8n: {erro}")
    workflows = (resposta or {}).get("data", resposta if isinstance(resposta, list) else [])
    return [
        {"id": str(w.get("id")), "name": w.get("name"), "active": bool(w.get("active")), "updatedAt": w.get("updatedAt"), "vinculado": str(w.get("id")) in vinculados}
        for w in workflows if todos or str(w.get("id")) in vinculados
    ]


@router.put("/integracoes/{cliente_id}/n8n/workflows")
def vincular_n8n_workflows(cliente_id: UUID, dados: N8nVinculosEntrada, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    item = obter_settings(db, usuario_id, cliente_id, True)
    integracoes = _integracoes(item)
    integracoes["n8n_workflow_ids"] = list(dict.fromkeys(dados.workflow_ids))
    item.integracoes = integracoes
    db.commit()
    return {"workflow_ids": integracoes["n8n_workflow_ids"]}


@router.post("/integracoes/{cliente_id}/n8n/workflows/{workflow_id}/{acao}")
async def acionar_n8n_workflow(cliente_id: UUID, workflow_id: str, acao: str, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    if acao not in {"activate", "deactivate"}:
        raise HTTPException(status_code=400, detail="Ação inválida.")
    item = obter_settings(db, usuario_id, cliente_id)
    if workflow_id not in _integracoes(item).get("n8n_workflow_ids", []):
        raise HTTPException(status_code=404, detail="Workflow não vinculado a este cliente.")
    try:
        resposta = await n8n("POST", f"workflows/{workflow_id}/{acao}")
    except IntegrationError as erro:
        raise HTTPException(status_code=502, detail=f"n8n: {erro}")
    return {"id": workflow_id, "active": acao == "activate", "dados": resposta}


@router.get("/integracoes/{cliente_id}/n8n/execucoes")
async def listar_n8n_execucoes(cliente_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    item = obter_settings(db, usuario_id, cliente_id)
    ids = _integracoes(item).get("n8n_workflow_ids", [])
    resultado = []
    try:
        for workflow_id in ids[:20]:
            resposta = await n8n("GET", "executions", params={"workflowId": workflow_id, "limit": 10})
            resultado.extend((resposta or {}).get("data", []))
    except IntegrationError as erro:
        raise HTTPException(status_code=502, detail=f"n8n: {erro}")
    resultado.sort(key=lambda x: x.get("startedAt") or "", reverse=True)
    return resultado[:50]
