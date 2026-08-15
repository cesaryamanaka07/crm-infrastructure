from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import obter_usuario_id
from app.database import get_db
from app.models import Cliente


router = APIRouter(prefix="/clientes", tags=["Clientes"])


class ClienteEntrada(BaseModel):
    nome: str = Field(min_length=2, max_length=255)


def _serializar(cliente: Cliente):
    return {"id": str(cliente.id), "nome": cliente.nome}


def _buscar(cliente_id: UUID, usuario_id: UUID, db: Session):
    cliente = db.scalar(select(Cliente).where(Cliente.id == cliente_id, Cliente.usuario_id == usuario_id))
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return cliente


@router.get("")
def listar_clientes(usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    clientes = db.scalars(select(Cliente).where(Cliente.usuario_id == usuario_id).order_by(Cliente.nome)).all()
    return [_serializar(cliente) for cliente in clientes]


@router.post("", status_code=201)
def criar_cliente(dados: ClienteEntrada, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    cliente = Cliente(usuario_id=usuario_id, nome=dados.nome.strip())
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return _serializar(cliente)


@router.put("/{cliente_id}")
def atualizar_cliente(cliente_id: UUID, dados: ClienteEntrada, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    cliente = _buscar(cliente_id, usuario_id, db)
    cliente.nome = dados.nome.strip()
    db.commit()
    return _serializar(cliente)


@router.delete("/{cliente_id}", status_code=204)
def excluir_cliente(cliente_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    cliente = _buscar(cliente_id, usuario_id, db)
    db.delete(cliente)
    db.commit()
