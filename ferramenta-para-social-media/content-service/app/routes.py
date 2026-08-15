import base64
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.auth import obter_usuario_id
from app.ai import OmniRouteError, gerar_imagens, gerar_textos
from app.database import get_db
from app.models import ArsenalCopy, Conteudo, GeracaoImagemSalva, GeracaoTexto, ImagemSalva, Tecnica
from app.schemas import (
    ConteudoCreate,
    ConteudoResponse,
    ConteudoUpdate,
    GeracaoImagemRequest,
    GeracaoImagemResponse,
    GeracaoHistoricoResponse,
    GeracaoResponse,
    GeracaoUpdate,
)


router = APIRouter(prefix="/conteudos", tags=["conteúdos"])


def validar_cliente(cliente_id: UUID | None, usuario_id: UUID, db: Session):
    if cliente_id is None:
        return
    existe = db.scalar(
        text(
            "SELECT EXISTS (SELECT 1 FROM social.clientes "
            "WHERE id=:cliente_id AND usuario_id=:usuario_id)"
        ),
        {"cliente_id": cliente_id, "usuario_id": usuario_id},
    )
    if not existe:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")


def buscar_tecnicas(slugs: list[str], db: Session) -> list[Tecnica]:
    if not slugs:
        return []
    tecnicas = db.scalars(select(Tecnica).where(Tecnica.slug.in_(slugs))).all()
    if len(tecnicas) != len(set(slugs)):
        raise HTTPException(status_code=422, detail="Uma ou mais técnicas são inválidas")
    tecnicas_por_slug = {tecnica.slug: tecnica for tecnica in tecnicas}
    return [tecnicas_por_slug[slug] for slug in dict.fromkeys(slugs)]


def buscar_conteudo_do_usuario(
    conteudo_id: UUID, usuario_id: UUID, db: Session
) -> Conteudo:
    conteudo = db.scalar(
        select(Conteudo).where(
            Conteudo.id == conteudo_id,
            Conteudo.usuario_id == usuario_id,
        )
    )
    if conteudo is None:
        raise HTTPException(status_code=404, detail="Conteúdo não encontrado")
    return conteudo


@router.post("", response_model=ConteudoResponse, status_code=status.HTTP_201_CREATED)
def criar_conteudo(
    dados: ConteudoCreate,
    usuario_id: UUID = Depends(obter_usuario_id),
    db: Session = Depends(get_db),
):
    valores = dados.model_dump()
    validar_cliente(valores.get("cliente_id"), usuario_id, db)
    slugs_tecnicas = valores.pop("tecnicas")
    conteudo = Conteudo(usuario_id=usuario_id, **valores)
    conteudo.tecnicas_rel = buscar_tecnicas(slugs_tecnicas, db)
    db.add(conteudo)
    db.commit()
    db.refresh(conteudo)
    return conteudo


@router.get("", response_model=list[ConteudoResponse])
def listar_conteudos(
    usuario_id: UUID = Depends(obter_usuario_id),
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Conteudo)
        .where(Conteudo.usuario_id == usuario_id)
        .order_by(Conteudo.atualizado_em.desc())
    ).all()


@router.get("/biblioteca")
def listar_biblioteca_conteudos(
    cliente_id: UUID | None = None,
    usuario_id: UUID = Depends(obter_usuario_id),
    db: Session = Depends(get_db),
):
    consulta = (
        select(GeracaoTexto, Conteudo)
        .join(Conteudo, Conteudo.id == GeracaoTexto.conteudo_id)
        .where(Conteudo.usuario_id == usuario_id)
    )
    if cliente_id is not None:
        consulta = consulta.where(Conteudo.cliente_id == cliente_id)
    registros = db.execute(consulta.order_by(GeracaoTexto.criado_em.desc())).all()
    consulta_midias = select(GeracaoImagemSalva).where(GeracaoImagemSalva.usuario_id == usuario_id)
    if cliente_id is not None:
        consulta_midias = consulta_midias.where(GeracaoImagemSalva.cliente_id == cliente_id)
    midias = db.scalars(consulta_midias.order_by(GeracaoImagemSalva.criado_em.desc())).all()
    imagens_por_geracao = {}
    for midia in midias:
        imagens = db.scalars(select(ImagemSalva).where(ImagemSalva.geracao_imagem_id == midia.id)).all()
        dados = [{
            "id": str(imagem.id), "nome": imagem.nome,
            "data_url": f"data:image/png;base64,{base64.b64encode(imagem.arquivo).decode('ascii')}",
        } for imagem in imagens]
        if midia.geracao_texto_id is not None and midia.conteudo_indice is not None:
            imagens_por_geracao.setdefault(str(midia.geracao_texto_id), {}).setdefault(str(midia.conteudo_indice), []).extend(dados)

    resultado = [
        {
            "id": str(geracao.id),
            "conteudo_id": str(conteudo.id),
            "cliente_id": str(conteudo.cliente_id) if conteudo.cliente_id else None,
            "tema": conteudo.tema,
            "modelo": geracao.modelo,
            "conteudos": geracao.conteudos,
            "imagens_por_post": imagens_por_geracao.get(str(geracao.id), {}),
            "criado_em": geracao.criado_em,
        }
        for geracao, conteudo in registros
    ]
    for midia in midias:
        if midia.geracao_texto_id is not None:
            continue
        imagens = db.scalars(select(ImagemSalva).where(ImagemSalva.geracao_imagem_id == midia.id)).all()
        resultado.append({
            "id": f"imagem-{midia.id}", "conteudo_id": None,
            "cliente_id": str(midia.cliente_id), "tema": midia.descricao,
            "modelo": midia.modelo, "conteudos": [], "formato_imagem": midia.formato,
            "imagens_avulsas": [{
                "id": str(imagem.id), "nome": imagem.nome,
                "data_url": f"data:image/png;base64,{base64.b64encode(imagem.arquivo).decode('ascii')}",
            } for imagem in imagens],
            "criado_em": midia.criado_em,
        })
    return sorted(resultado, key=lambda item: item["criado_em"], reverse=True)


@router.get("/{conteudo_id}", response_model=ConteudoResponse)
def detalhar_conteudo(
    conteudo_id: UUID,
    usuario_id: UUID = Depends(obter_usuario_id),
    db: Session = Depends(get_db),
):
    return buscar_conteudo_do_usuario(conteudo_id, usuario_id, db)


@router.post("/{conteudo_id}/gerar", response_model=GeracaoResponse)
async def gerar_conteudo(
    conteudo_id: UUID,
    usuario_id: UUID = Depends(obter_usuario_id),
    db: Session = Depends(get_db),
):
    conteudo = buscar_conteudo_do_usuario(conteudo_id, usuario_id, db)
    arsenal = None
    if conteudo.cliente_id:
        arsenal = db.scalar(select(ArsenalCopy).where(
            ArsenalCopy.usuario_id == usuario_id,
            ArsenalCopy.cliente_id == conteudo.cliente_id,
        ))
    if arsenal:
        selecionadas = [
            f"{campo}: {arsenal.informacoes.get(campo)}"
            for campo in conteudo.arsenal_campos
            if arsenal.informacoes.get(campo)
        ]
        conteudo.contexto_arsenal = "\n".join(selecionadas)
        conteudo.manual_arsenal = arsenal.manual_ia
    try:
        modelo, itens = await gerar_textos(conteudo)
        resposta = GeracaoResponse(
            conteudo_id=conteudo.id,
            modelo=modelo,
            conteudos=itens,
        )
    except OmniRouteError as erro:
        raise HTTPException(status_code=502, detail=str(erro)) from erro
    except ValueError as erro:
        raise HTTPException(
            status_code=502,
            detail="A IA retornou conteúdo fora do formato esperado",
        ) from erro
    geracao = GeracaoTexto(
        conteudo_id=conteudo.id,
        modelo=resposta.modelo,
        conteudos=[item.model_dump(mode="json") for item in resposta.conteudos],
    )
    db.add(geracao)
    conteudo.status = "pronto_para_gerar"
    db.commit()
    return resposta


@router.get(
    "/{conteudo_id}/geracoes",
    response_model=list[GeracaoHistoricoResponse],
)
def listar_geracoes_conteudo(
    conteudo_id: UUID,
    usuario_id: UUID = Depends(obter_usuario_id),
    db: Session = Depends(get_db),
):
    buscar_conteudo_do_usuario(conteudo_id, usuario_id, db)
    return db.scalars(
        select(GeracaoTexto)
        .where(GeracaoTexto.conteudo_id == conteudo_id)
        .order_by(GeracaoTexto.criado_em.desc())
    ).all()


@router.delete(
    "/{conteudo_id}/geracoes/{geracao_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def excluir_geracao_conteudo(
    conteudo_id: UUID,
    geracao_id: UUID,
    usuario_id: UUID = Depends(obter_usuario_id),
    db: Session = Depends(get_db),
):
    buscar_conteudo_do_usuario(conteudo_id, usuario_id, db)
    geracao = db.scalar(
        select(GeracaoTexto).where(
            GeracaoTexto.id == geracao_id,
            GeracaoTexto.conteudo_id == conteudo_id,
        )
    )
    if geracao is None:
        raise HTTPException(status_code=404, detail="Geração não encontrada")
    db.delete(geracao)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/{conteudo_id}/geracoes/{geracao_id}",
    response_model=GeracaoHistoricoResponse,
)
def atualizar_geracao_conteudo(
    conteudo_id: UUID,
    geracao_id: UUID,
    dados: GeracaoUpdate,
    usuario_id: UUID = Depends(obter_usuario_id),
    db: Session = Depends(get_db),
):
    buscar_conteudo_do_usuario(conteudo_id, usuario_id, db)
    geracao = db.scalar(select(GeracaoTexto).where(
        GeracaoTexto.id == geracao_id,
        GeracaoTexto.conteudo_id == conteudo_id,
    ))
    if geracao is None:
        raise HTTPException(status_code=404, detail="Geração não encontrada")
    geracao.conteudos = [item.model_dump(mode="json") for item in dados.conteudos]
    db.commit(); db.refresh(geracao)
    return geracao


@router.post("/{conteudo_id}/gerar-imagens", response_model=GeracaoImagemResponse)
async def gerar_imagem_do_conteudo(
    conteudo_id: UUID,
    dados: GeracaoImagemRequest,
    usuario_id: UUID = Depends(obter_usuario_id),
    db: Session = Depends(get_db),
):
    conteudo = buscar_conteudo_do_usuario(conteudo_id, usuario_id, db)
    try:
        modelo, imagens = await gerar_imagens(conteudo, dados)
        return GeracaoImagemResponse(
            conteudo_id=conteudo.id,
            modelo=modelo,
            imagens=imagens,
        )
    except OmniRouteError as erro:
        raise HTTPException(status_code=502, detail=str(erro)) from erro
    except ValueError as erro:
        raise HTTPException(
            status_code=502,
            detail="A IA retornou uma imagem fora do formato esperado",
        ) from erro


@router.patch("/{conteudo_id}", response_model=ConteudoResponse)
def atualizar_conteudo(
    conteudo_id: UUID,
    dados: ConteudoUpdate,
    usuario_id: UUID = Depends(obter_usuario_id),
    db: Session = Depends(get_db),
):
    conteudo = buscar_conteudo_do_usuario(conteudo_id, usuario_id, db)
    valores = dados.model_dump(exclude_unset=True)
    if "cliente_id" in valores:
        validar_cliente(valores["cliente_id"], usuario_id, db)
    if "tecnicas" in valores:
        conteudo.tecnicas_rel = buscar_tecnicas(valores.pop("tecnicas"), db)
    for campo, valor in valores.items():
        setattr(conteudo, campo, valor)
    db.commit()
    db.refresh(conteudo)
    return conteudo


@router.delete("/{conteudo_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_conteudo(
    conteudo_id: UUID,
    usuario_id: UUID = Depends(obter_usuario_id),
    db: Session = Depends(get_db),
):
    conteudo = buscar_conteudo_do_usuario(conteudo_id, usuario_id, db)
    db.delete(conteudo)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
