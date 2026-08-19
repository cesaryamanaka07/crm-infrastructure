import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, Integer, JSON, LargeBinary, String, Text, Uuid, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class AutomationFlow(Base):
    __tablename__ = "fluxos"; __table_args__ = {"schema": "automation"}
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    cliente_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    canal: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="rascunho")
    blocos: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    conexoes: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    proximo_numero: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Contact(Base):
    __tablename__ = "contatos"; __table_args__ = {"schema": "automation"}
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    cliente_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    canal: Mapped[str] = mapped_column(String(20), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    sobrenome: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    telefone: Mapped[str | None] = mapped_column(String(40))
    email: Mapped[str | None] = mapped_column(String(255))
    instagram_usuario: Mapped[str | None] = mapped_column(String(255))
    facebook_usuario: Mapped[str | None] = mapped_column(String(255))
    etapa_id: Mapped[str | None] = mapped_column(String(100))
    qualidade_id: Mapped[str | None] = mapped_column(String(100))
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    respostas: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class AutomationSettings(Base):
    __tablename__ = "configuracoes"; __table_args__ = (UniqueConstraint("usuario_id", "cliente_id"), {"schema": "automation"})
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    cliente_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    cores: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    crm_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    integracoes: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    google_calendar_id: Mapped[str | None] = mapped_column(String(320), nullable=True)
    google_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    google_access_token: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    google_refresh_token: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    google_token_expira_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class CrmActivity(Base):
    __tablename__ = "atividades"; __table_args__ = {"schema": "automation"}
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    cliente_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    contato_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True, index=True)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False, default="tarefa")
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False, default="")
    inicio_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fim_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    google_event_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    convidados: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    concluida: Mapped[bool] = mapped_column(nullable=False, default=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
