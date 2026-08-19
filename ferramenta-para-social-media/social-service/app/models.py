import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, LargeBinary, String, Text, Uuid, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class OAuthState(Base):
    __tablename__ = "oauth_states"
    __table_args__ = {"schema": "social"}

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    state_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    usuario_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    cliente_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("social.clientes.id", ondelete="CASCADE"), nullable=True, index=True
    )
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SocialConnection(Base):
    __tablename__ = "conexoes"
    __table_args__ = (
        UniqueConstraint("usuario_id", "provider", "external_id"),
        {"schema": "social"},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    cliente_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("social.clientes.id", ondelete="CASCADE"), nullable=True, index=True
    )
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    access_token: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    refresh_token: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    scopes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    selecionada: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    expira_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    conectado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Cliente(Base):
    __tablename__ = "clientes"
    __table_args__ = {"schema": "social"}

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class GoogleConnection(Base):
    __tablename__ = "google_conexoes"; __table_args__ = (UniqueConstraint("usuario_id", "cliente_id"), {"schema": "social"})
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    cliente_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("social.clientes.id", ondelete="CASCADE"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    access_token: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    refresh_token: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    expira_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
