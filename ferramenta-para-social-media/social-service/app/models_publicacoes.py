import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, LargeBinary, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Publicacao(Base):
    __tablename__ = "publicacoes"
    __table_args__ = {"schema": "social"}
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    cliente_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("social.clientes.id", ondelete="CASCADE"), nullable=False, index=True)
    formato: Mapped[str] = mapped_column(String(30), nullable=False)
    titulo: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    legenda: Mapped[str] = mapped_column(Text, nullable=False, default="")
    hashtags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    roteiro: Mapped[str | None] = mapped_column(Text, nullable=True)
    duracao_segundos: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="rascunho", index=True)
    publicar_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class PublicacaoItem(Base):
    __tablename__ = "publicacao_itens"
    __table_args__ = {"schema": "social"}
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    publicacao_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("social.publicacoes.id", ondelete="CASCADE"), nullable=False, index=True)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    titulo: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    arquivo: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    nome_arquivo: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(120), nullable=False)


class PublicacaoRede(Base):
    __tablename__ = "publicacao_redes"
    __table_args__ = {"schema": "social"}
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    publicacao_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("social.publicacoes.id", ondelete="CASCADE"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    conexao_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("social.conexoes.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pendente", index=True)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    erro: Mapped[str | None] = mapped_column(Text, nullable=True)
    publicado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class PublicacaoIdeia(Base):
    __tablename__ = "publicacao_ideias"
    __table_args__ = {"schema": "social"}
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    publicacao_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("social.publicacoes.id", ondelete="CASCADE"), nullable=False, unique=True)
    ideia_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


__all__ = ["Publicacao", "PublicacaoItem", "PublicacaoRede", "PublicacaoIdeia"]
