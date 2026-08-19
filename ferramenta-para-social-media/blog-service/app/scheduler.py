import asyncio
from datetime import datetime, timezone
from sqlalchemy import select
from app.database import SessionLocal
from app.models import IdeiaBlog
from app.routes import obter_integracao, processar_ideia
from app.integrations import publicar_wordpress


async def executar_agenda(intervalo):
    while True:
        await asyncio.sleep(max(intervalo, 15))
        with SessionLocal() as db:
            ideias = db.scalars(select(IdeiaBlog).where(IdeiaBlog.status == "agendada", IdeiaBlog.agendado_para <= datetime.now(timezone.utc)).with_for_update(skip_locked=True).limit(5)).all()
            for ideia in ideias:
                ideia.status = "processando"; db.commit()
                try:
                    artigo = await processar_ideia(db, ideia)
                    if ideia.destino_wordpress in {"draft", "publish"}:
                        integracao = obter_integracao(db, ideia.usuario_id, ideia.cliente_id)
                        if not integracao:
                            raise ValueError("Integração WordPress do cliente não configurada")
                        post_id, url = await publicar_wordpress(integracao, artigo, ideia.destino_wordpress)
                        artigo.wordpress_post_id = post_id; artigo.wordpress_url = url
                        artigo.status = "publicado" if ideia.destino_wordpress == "publish" else "rascunho_wordpress"
                        if ideia.destino_wordpress == "publish": artigo.publicado_em = datetime.now(timezone.utc)
                        db.commit()
                except Exception as erro:
                    ideia.status = "erro"; ideia.erro = str(erro)[:2000]; db.commit()
