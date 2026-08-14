import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = {"schema": "auth"}  # usa o schema "auth" dentro do PostgreSQL

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))