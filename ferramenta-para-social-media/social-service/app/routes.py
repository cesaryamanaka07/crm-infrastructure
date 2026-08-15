from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.auth import obter_usuario_id
from app.database import get_db
from app.models import SocialConnection


router = APIRouter()


@router.get("/conexoes")
def listar_conexoes(usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    itens = db.scalars(select(SocialConnection).where(SocialConnection.usuario_id == usuario_id)).all()
    return [{"id": str(item.id), "provider": item.provider, "nome": item.nome,
             "cliente_id": str(item.cliente_id) if item.cliente_id else None,
             "external_id": item.external_id, "expira_em": item.expira_em,
             "conectado_em": item.conectado_em, "selecionada": item.selecionada} for item in itens]


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
