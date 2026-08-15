from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.auth import obter_usuario_id
from app.database import get_db
from app.models import ArsenalCopy


router = APIRouter(prefix="/arsenais", tags=["arsenal de copy"])


class ArsenalDados(BaseModel):
    informacoes: dict[str, str] = Field(default_factory=dict)
    manual_ia: str | None = Field(default=None, max_length=15000)


def validar_cliente(cliente_id: UUID, usuario_id: UUID, db: Session):
    existe = db.scalar(text(
        "SELECT EXISTS (SELECT 1 FROM social.clientes WHERE id=:cliente_id AND usuario_id=:usuario_id)"
    ), {"cliente_id": cliente_id, "usuario_id": usuario_id})
    if not existe:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")


@router.get("/{cliente_id}")
def obter_arsenal(cliente_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    validar_cliente(cliente_id, usuario_id, db)
    arsenal = db.scalar(select(ArsenalCopy).where(
        ArsenalCopy.usuario_id == usuario_id, ArsenalCopy.cliente_id == cliente_id
    ))
    if arsenal is None:
        return {"cliente_id": str(cliente_id), "informacoes": {}, "manual_ia": ""}
    return {"id": str(arsenal.id), "cliente_id": str(cliente_id), "informacoes": arsenal.informacoes, "manual_ia": arsenal.manual_ia or "", "atualizado_em": arsenal.atualizado_em}


@router.put("/{cliente_id}")
def salvar_arsenal(cliente_id: UUID, dados: ArsenalDados, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    validar_cliente(cliente_id, usuario_id, db)
    informacoes = {
        chave: valor.strip() for chave, valor in dados.informacoes.items()
        if isinstance(chave, str) and isinstance(valor, str) and valor.strip()
    }
    if any(len(chave) > 80 or len(valor) > 10000 for chave, valor in informacoes.items()):
        raise HTTPException(status_code=422, detail="Uma informação do Arsenal ultrapassou o limite")
    arsenal = db.scalar(select(ArsenalCopy).where(
        ArsenalCopy.usuario_id == usuario_id, ArsenalCopy.cliente_id == cliente_id
    ))
    if arsenal is None:
        arsenal = ArsenalCopy(usuario_id=usuario_id, cliente_id=cliente_id)
        db.add(arsenal)
    arsenal.informacoes = informacoes
    arsenal.manual_ia = dados.manual_ia.strip() if dados.manual_ia else None
    db.commit(); db.refresh(arsenal)
    return {"id": str(arsenal.id), "cliente_id": str(cliente_id), "informacoes": arsenal.informacoes, "manual_ia": arsenal.manual_ia or "", "atualizado_em": arsenal.atualizado_em}
