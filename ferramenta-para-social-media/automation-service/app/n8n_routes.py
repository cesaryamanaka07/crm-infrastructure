from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import obter_usuario_id
from app.database import get_db
from app.integrations import IntegrationError, n8n
from app.models import AutomationSettings
from app.n8n_templates import workflow_inicial

router = APIRouter()


class N8nWorkflowEntrada(BaseModel):
    nome: str = Field(min_length=2, max_length=120)


def _integracoes(item):
    return dict(item.integracoes or {}) if item else {}


@router.post("/integracoes/{cliente_id}/n8n/workflows", status_code=201)
async def criar_n8n_workflow(
    cliente_id: UUID,
    dados: N8nWorkflowEntrada,
    usuario_id: UUID = Depends(obter_usuario_id),
    db: Session = Depends(get_db),
):
    item = db.scalar(
        select(AutomationSettings).where(
            AutomationSettings.usuario_id == usuario_id,
            AutomationSettings.cliente_id == cliente_id,
        )
    )
    if not item:
        item = AutomationSettings(
            usuario_id=usuario_id,
            cliente_id=cliente_id,
            cores={},
            crm_config={},
            integracoes={},
        )
        db.add(item)

    try:
        resposta = await n8n("POST", "workflows", payload=workflow_inicial(dados.nome.strip()))
    except IntegrationError as erro:
        status = 503 if erro.status_code is None else 502
        raise HTTPException(status_code=status, detail=f"n8n: {erro}") from erro

    workflow_id = str((resposta or {}).get("id") or "")
    if not workflow_id:
        raise HTTPException(status_code=502, detail="n8n: a API não retornou o ID do workflow criado.")

    integracoes = _integracoes(item)
    ids = list(integracoes.get("n8n_workflow_ids", []))
    if workflow_id not in ids:
        ids.append(workflow_id)
    integracoes["n8n_workflow_ids"] = ids
    item.integracoes = integracoes
    db.commit()

    return {
        "id": workflow_id,
        "name": resposta.get("name", dados.nome.strip()),
        "active": bool(resposta.get("active", False)),
        "vinculado": True,
        "dados": resposta,
    }
