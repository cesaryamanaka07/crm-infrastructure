from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
import httpx
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import obter_usuario_id
from app.database import get_db
from app.models import Cliente, GoogleConnection
from app.config import settings
from app.crypto import criptografar


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
    conexoes = {x.cliente_id:x for x in db.scalars(select(GoogleConnection).where(GoogleConnection.usuario_id == usuario_id)).all()}
    return [{**_serializar(c), "google_conectado": c.id in conexoes, "google_email": conexoes[c.id].email if c.id in conexoes else None} for c in clientes]

@router.get("/{cliente_id}/google/iniciar")
def iniciar_google(cliente_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    _buscar(cliente_id, usuario_id, db)
    if not settings.google_oauth_client_id or not settings.google_oauth_client_secret: raise HTTPException(503,"Configure o OAuth Google no social-service")
    state=jwt.encode({"sub":str(usuario_id),"cliente_id":str(cliente_id),"exp":datetime.now(timezone.utc)+timedelta(minutes=10)},settings.secret_key,algorithm=settings.algorithm)
    scopes="openid email https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/spreadsheets https://www.googleapis.com/auth/drive.metadata.readonly"
    return {"url":"https://accounts.google.com/o/oauth2/v2/auth?"+urlencode({"client_id":settings.google_oauth_client_id,"redirect_uri":settings.google_oauth_redirect_uri,"response_type":"code","scope":scopes,"access_type":"offline","prompt":"consent select_account","state":state})}

@router.get("/google/callback")
async def callback_google(code: str|None=None,state: str|None=None,error: str|None=None,db: Session=Depends(get_db)):
    destino=settings.frontend_return_url.rstrip("/")+"/clientes"
    if error or not code or not state:return RedirectResponse(destino+"?google=cancelado")
    try:
        dados=jwt.decode(state,settings.secret_key,algorithms=[settings.algorithm]); usuario_id=UUID(dados["sub"]); cliente_id=UUID(dados["cliente_id"])
        async with httpx.AsyncClient(timeout=30) as c:
            r=await c.post("https://oauth2.googleapis.com/token",data={"code":code,"client_id":settings.google_oauth_client_id,"client_secret":settings.google_oauth_client_secret,"redirect_uri":settings.google_oauth_redirect_uri,"grant_type":"authorization_code"}); r.raise_for_status(); t=r.json()
            p=await c.get("https://openidconnect.googleapis.com/v1/userinfo",headers={"Authorization":f"Bearer {t['access_token']}"});p.raise_for_status()
        item=db.scalar(select(GoogleConnection).where(GoogleConnection.usuario_id==usuario_id,GoogleConnection.cliente_id==cliente_id))
        if not item:item=GoogleConnection(usuario_id=usuario_id,cliente_id=cliente_id,email=p.json()["email"],access_token=b"",refresh_token=b"");db.add(item)
        item.email=p.json()["email"];item.access_token=criptografar(t["access_token"])
        if t.get("refresh_token"):item.refresh_token=criptografar(t["refresh_token"])
        item.expira_em=datetime.now(timezone.utc)+timedelta(seconds=t.get("expires_in",3600));db.commit()
    except Exception:return RedirectResponse(destino+"?google=erro")
    return RedirectResponse(destino+"?google=conectado")

@router.delete("/{cliente_id}/google",status_code=204)
def desconectar_google(cliente_id:UUID,usuario_id:UUID=Depends(obter_usuario_id),db:Session=Depends(get_db)):
    item=db.scalar(select(GoogleConnection).where(GoogleConnection.usuario_id==usuario_id,GoogleConnection.cliente_id==cliente_id))
    if item:db.delete(item);db.commit()


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
