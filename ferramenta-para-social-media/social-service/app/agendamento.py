import asyncio
from datetime import datetime, timezone
from sqlalchemy import select
from app.database import SessionLocal
from app.models_publicacoes import Publicacao
from app.publicacoes_routes import publicar_por_id


async def executar_agendamento():
    while True:
        try:
            with SessionLocal() as db:
                agora = datetime.now(timezone.utc)
                itens = db.scalars(select(Publicacao).where(Publicacao.status == "agendada", Publicacao.publicar_em <= agora).limit(10)).all()
                for item in itens:
                    item.status = "processando"
                    db.commit()
                    await publicar_por_id(item.id, item.usuario_id, db)
        except Exception:
            pass
        await asyncio.sleep(30)
