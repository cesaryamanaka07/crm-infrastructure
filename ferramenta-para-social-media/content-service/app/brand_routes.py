import base64
import json
import re
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.auth import obter_usuario_id
from app.database import get_db
from app.models import LogoMarca, Marca


router = APIRouter(prefix="/marcas", tags=["marcas"])
MIMES_LOGO = {"image/png", "image/jpeg", "image/webp"}
COR_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def _validar_cliente(cliente_id: UUID, usuario_id: UUID, db: Session):
    existe = db.scalar(text(
        "SELECT EXISTS (SELECT 1 FROM social.clientes WHERE id=:cliente_id AND usuario_id=:usuario_id)"
    ), {"cliente_id": cliente_id, "usuario_id": usuario_id})
    if not existe:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")


def _data_url(arquivo: bytes, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode(arquivo).decode('ascii')}"


def _resposta(marca: Marca) -> dict:
    logos = [{"id": str(item.id), "data_url": _data_url(item.arquivo, item.mime)} for item in marca.logos]
    return {
        "id": str(marca.id), "cliente_id": str(marca.cliente_id),
        "paleta": marca.paleta, "tipografia": marca.tipografia,
        "diretrizes_visuais": marca.diretrizes_visuais or {},
        "logos": logos, "atualizado_em": marca.atualizado_em,
    }


@router.get("/{cliente_id}")
def obter_marca(cliente_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    _validar_cliente(cliente_id, usuario_id, db)
    marca = db.scalar(select(Marca).where(Marca.usuario_id == usuario_id, Marca.cliente_id == cliente_id))
    if marca is None:
        raise HTTPException(status_code=404, detail="Identidade da marca não configurada")
    return _resposta(marca)


@router.delete("/{cliente_id}/logos/{logo_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_logo(
    cliente_id: UUID,
    logo_id: UUID,
    usuario_id: UUID = Depends(obter_usuario_id),
    db: Session = Depends(get_db),
):
    _validar_cliente(cliente_id, usuario_id, db)
    logo = db.scalar(
        select(LogoMarca)
        .join(Marca, Marca.id == LogoMarca.marca_id)
        .where(
            LogoMarca.id == logo_id,
            Marca.cliente_id == cliente_id,
            Marca.usuario_id == usuario_id,
        )
    )
    if logo is None:
        raise HTTPException(status_code=404, detail="Logotipo não encontrado")
    db.delete(logo); db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{cliente_id}")
async def salvar_marca(
    cliente_id: UUID,
    paleta: str = Form(...),
    tipografia: str = Form(..., min_length=2, max_length=120),
    diretrizes_visuais: str = Form(default="{}"),
    logos: list[UploadFile] = File(default=[]),
    remover_logos: bool = Form(default=False),
    usuario_id: UUID = Depends(obter_usuario_id),
    db: Session = Depends(get_db),
):
    _validar_cliente(cliente_id, usuario_id, db)
    try:
        cores = json.loads(paleta)
    except json.JSONDecodeError as erro:
        raise HTTPException(status_code=422, detail="Paleta inválida") from erro
    if not isinstance(cores, list) or not 1 <= len(cores) <= 8:
        raise HTTPException(status_code=422, detail="Informe de 1 a 8 cores")
    if any(not isinstance(cor, str) or not COR_HEX.match(cor) for cor in cores):
        raise HTTPException(status_code=422, detail="Use cores no formato hexadecimal #RRGGBB")
    try:
        diretrizes = json.loads(diretrizes_visuais)
    except json.JSONDecodeError as erro:
        raise HTTPException(status_code=422, detail="Diretrizes visuais inválidas") from erro
    if not isinstance(diretrizes, dict) or any(
        not isinstance(chave, str) or not isinstance(valor, str) or len(valor) > 5000
        for chave, valor in diretrizes.items()
    ):
        raise HTTPException(status_code=422, detail="Diretrizes visuais inválidas")
    diretrizes = {chave: valor.strip() for chave, valor in diretrizes.items() if valor.strip()}

    marca = db.scalar(select(Marca).where(Marca.usuario_id == usuario_id, Marca.cliente_id == cliente_id))
    if marca is None:
        marca = Marca(usuario_id=usuario_id, cliente_id=cliente_id, paleta=cores, tipografia=tipografia, diretrizes_visuais=diretrizes)
        db.add(marca); db.flush()
    else:
        marca.paleta = cores; marca.tipografia = tipografia; marca.diretrizes_visuais = diretrizes

    if remover_logos:
        marca.logos.clear()
    if len(logos) > 6:
        raise HTTPException(status_code=422, detail="Envie no máximo 6 logotipos")
    for logo in logos:
        if logo.content_type not in MIMES_LOGO:
            raise HTTPException(status_code=422, detail="Os logotipos devem ser PNG, JPEG ou WebP")
        dados = await logo.read(2 * 1024 * 1024 + 1)
        if len(dados) > 2 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Cada logotipo deve ter no máximo 2 MB")
        marca.logos.append(LogoMarca(arquivo=dados, mime=logo.content_type))
    if len(marca.logos) > 6:
        raise HTTPException(status_code=422, detail="A marca pode ter no máximo 6 logotipos")

    db.commit(); db.refresh(marca)
    return _resposta(marca)
