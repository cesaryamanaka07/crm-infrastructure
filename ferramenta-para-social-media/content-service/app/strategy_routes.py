import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.ai import OmniRouteError, gerar_json_estrategico
from app.auth import obter_usuario_id
from app.database import get_db
from app.models import ArsenalCopy, LinhaEditorial, NarrativaEstrategica
from app.schemas import BriefingLinhaRequest

router = APIRouter(prefix="/estrategias", tags=["estratégia"])


def contexto(cliente_id: UUID, usuario_id: UUID, db: Session):
    cliente = db.execute(text("SELECT nome FROM social.clientes WHERE id=:id AND usuario_id=:uid"), {"id": cliente_id, "uid": usuario_id}).first()
    if not cliente: raise HTTPException(status_code=404, detail="Cliente não encontrado")
    arsenal = db.scalar(select(ArsenalCopy).where(ArsenalCopy.cliente_id == cliente_id, ArsenalCopy.usuario_id == usuario_id))
    conexoes = db.execute(text("SELECT provider, nome FROM social.conexoes WHERE cliente_id=:id AND usuario_id=:uid"), {"id": cliente_id, "uid": usuario_id}).all()
    return cliente[0], arsenal, [{"rede": item[0], "conta": item[1]} for item in conexoes]


@router.get("/{cliente_id}/narrativa")
def obter_narrativa(cliente_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    item = db.scalar(select(NarrativaEstrategica).where(NarrativaEstrategica.cliente_id == cliente_id, NarrativaEstrategica.usuario_id == usuario_id))
    return {"resultado": item.resultado, "atualizado_em": item.atualizado_em} if item else {"resultado": None}


@router.post("/{cliente_id}/narrativa")
async def gerar_narrativa(cliente_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    nome, arsenal, conexoes = contexto(cliente_id, usuario_id, db)
    if not arsenal or not arsenal.informacoes: raise HTTPException(status_code=422, detail="Preencha o Arsenal de Copy deste cliente primeiro")
    prompt = f"""Crie um Diagnóstico de Perfil e uma Narrativa Estratégica de Conversão para {nome}.
Arsenal de Copy: {json.dumps(arsenal.informacoes, ensure_ascii=False)}
Manual: {arsenal.manual_ia or 'nenhum'}
Contas conectadas: {json.dumps(conexoes, ensure_ascii=False)}
Entregue JSON com: diagnostico (gargalos, curiosos_vs_compradores, ajuste_imediato), narrativa_central (gancho_conexao, inimigo_comum, ponto_virada, mecanismo_unico, mensagem_principal), posicionamento, pilares_conteudo, tom_comunicacao, jornada_seguidor_cliente e metricas_roi. Seja direto, prático e orientado a conversão."""
    try: modelo, resultado = await gerar_json_estrategico("Você é Estrategista de Conteúdo sênior e Copywriter especialista em Vendas Diretas e Storytelling. Responda somente JSON válido em português brasileiro.", prompt)
    except OmniRouteError as erro: raise HTTPException(status_code=502, detail=str(erro)) from erro
    item = db.scalar(select(NarrativaEstrategica).where(NarrativaEstrategica.cliente_id == cliente_id, NarrativaEstrategica.usuario_id == usuario_id))
    if not item: item = NarrativaEstrategica(cliente_id=cliente_id, usuario_id=usuario_id, resultado=resultado); db.add(item)
    else: item.resultado = resultado
    db.commit(); db.refresh(item); return {"modelo": modelo, "resultado": item.resultado, "atualizado_em": item.atualizado_em}


@router.get("/{cliente_id}/linha-editorial")
def obter_linha(cliente_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    item = db.scalar(select(LinhaEditorial).where(LinhaEditorial.cliente_id == cliente_id, LinhaEditorial.usuario_id == usuario_id))
    return {"resultado": item.resultado, "atualizado_em": item.atualizado_em} if item else {"resultado": None}


@router.post("/{cliente_id}/linha-editorial")
async def gerar_linha(cliente_id: UUID, usuario_id: UUID = Depends(obter_usuario_id), db: Session = Depends(get_db)):
    nome, arsenal, _ = contexto(cliente_id, usuario_id, db)
    narrativa = db.scalar(select(NarrativaEstrategica).where(NarrativaEstrategica.cliente_id == cliente_id, NarrativaEstrategica.usuario_id == usuario_id))
    if not narrativa: raise HTTPException(status_code=422, detail="Gere a Narrativa Estratégica deste cliente primeiro")
    prompt = f"""Crie uma Linha Editorial de Funil para {nome}, baseada nesta narrativa: {json.dumps(narrativa.resultado, ensure_ascii=False)} e neste Arsenal: {json.dumps(arsenal.informacoes if arsenal else {}, ensure_ascii=False)}.
Responda JSON com topo_funil (3 ou mais ideias para atração qualificada), meio_funil (3 ou mais ideias para nutrição e autoridade), fundo_funil (3 ou mais ideias para conversão e oferta), calendario_recomendado, ctas_por_etapa e script_story_vendas contendo de 5 a 7 telas. Cada ideia deve conter título, objetivo, formato, gancho e CTA. Priorize ROI."""
    try: modelo, resultado = await gerar_json_estrategico("Você cria planos editoriais de funil orientados a vendas. Responda somente JSON válido em português brasileiro.", prompt)
    except OmniRouteError as erro: raise HTTPException(status_code=502, detail=str(erro)) from erro
    item = db.scalar(select(LinhaEditorial).where(LinhaEditorial.cliente_id == cliente_id, LinhaEditorial.usuario_id == usuario_id))
    if not item: item = LinhaEditorial(cliente_id=cliente_id, usuario_id=usuario_id, resultado=resultado); db.add(item)
    else: item.resultado = resultado
    db.commit(); db.refresh(item); return {"modelo": modelo, "resultado": item.resultado, "atualizado_em": item.atualizado_em}


@router.post("/{cliente_id}/briefing-conteudo")
async def gerar_briefing_conteudo(
    cliente_id: UUID,
    dados: BriefingLinhaRequest,
    usuario_id: UUID = Depends(obter_usuario_id),
    db: Session = Depends(get_db),
):
    nome, arsenal, _ = contexto(cliente_id, usuario_id, db)
    narrativa = db.scalar(select(NarrativaEstrategica).where(
        NarrativaEstrategica.cliente_id == cliente_id,
        NarrativaEstrategica.usuario_id == usuario_id,
    ))
    ideia = dados.ideia
    prompt = f"""Transforme a ideia editorial abaixo em um briefing objetivo para criar conteúdo para {nome}.
Ideia da Linha Editorial: {json.dumps(ideia, ensure_ascii=False)}
Arsenal de Copy completo do cliente: {json.dumps(arsenal.informacoes if arsenal else {}, ensure_ascii=False)}
Manual permanente: {arsenal.manual_ia if arsenal else 'nenhum'}
Narrativa Estratégica: {json.dumps(narrativa.resultado if narrativa else {}, ensure_ascii=False)}

Responda somente JSON válido, sem Markdown, exatamente neste formato:
{{"tema":"...", "intencao":"...", "perspectiva":"..."}}
O tema deve ser específico, a intenção deve explicar o resultado desejado e a perspectiva deve definir o ângulo para o público. Use português brasileiro e não invente dados fora do contexto."""
    try:
        modelo, resultado = await gerar_json_estrategico(
            "Você é um estrategista editorial. Responda somente JSON válido com tema, intencao e perspectiva.",
            prompt,
        )
    except OmniRouteError as erro:
        raise HTTPException(status_code=502, detail=str(erro)) from erro
    campos = {chave: str(resultado.get(chave, '')).strip() for chave in ('tema', 'intencao', 'perspectiva')}
    if any(len(valor) < 3 for valor in campos.values()):
        raise HTTPException(status_code=502, detail="A IA não retornou um briefing completo")
    return {"modelo": modelo, **campos}
