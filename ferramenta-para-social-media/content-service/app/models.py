import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, ForeignKey, LargeBinary, String, Table, Text, Uuid, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


conteudo_tecnicas = Table(
    "conteudo_tecnicas",
    Base.metadata,
    Column(
        "conteudo_id",
        Uuid(as_uuid=True),
        ForeignKey("content.conteudos.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tecnica_id",
        Uuid(as_uuid=True),
        ForeignKey("content.tecnicas.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    schema="content",
)


class Tecnica(Base):
    __tablename__ = "tecnicas"
    __table_args__ = {"schema": "content"}

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)


class Conteudo(Base):
    __tablename__ = "conteudos"
    __table_args__ = {"schema": "content"}

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    cliente_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True, index=True
    )
    intencao: Mapped[str] = mapped_column(String(500), nullable=False)
    tema: Mapped[str] = mapped_column(String(300), nullable=False)
    perspectiva: Mapped[str] = mapped_column(String(500), nullable=False)
    modelo: Mapped[str] = mapped_column(String(80), nullable=False)
    tom_de_voz: Mapped[str] = mapped_column(String(80), nullable=False)
    formato: Mapped[str] = mapped_column(String(30), nullable=False)
    quantidades: Mapped[dict] = mapped_column(JSON, nullable=False)
    narrativas: Mapped[dict] = mapped_column(JSON, nullable=False)
    tamanho_legenda: Mapped[str] = mapped_column(
        String(20), nullable=False, default="media"
    )
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    arsenal_campos: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    instrucoes_ia: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="rascunho")
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    tecnicas_rel: Mapped[list[Tecnica]] = relationship(
        secondary=conteudo_tecnicas,
        lazy="selectin",
    )

    @property
    def tecnicas(self) -> list[str]:
        return [tecnica.slug for tecnica in self.tecnicas_rel]


class GeracaoTexto(Base):
    __tablename__ = "geracoes_texto"
    __table_args__ = {"schema": "content"}

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    conteudo_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("content.conteudos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    modelo: Mapped[str] = mapped_column(String(120), nullable=False)
    conteudos: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class GeracaoImagemSalva(Base):
    __tablename__ = "geracoes_imagem"
    __table_args__ = {"schema": "content"}

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    cliente_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    geracao_texto_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("content.geracoes_texto.id", ondelete="SET NULL"), nullable=True, index=True
    )
    conteudo_indice: Mapped[int | None] = mapped_column(nullable=True)
    formato: Mapped[str] = mapped_column(String(30), nullable=False)
    tamanho: Mapped[str] = mapped_column(String(20), nullable=False)
    modelo: Mapped[str] = mapped_column(String(120), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ImagemSalva(Base):
    __tablename__ = "imagens_salvas"
    __table_args__ = {"schema": "content"}

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    geracao_imagem_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("content.geracoes_imagem.id", ondelete="CASCADE"), nullable=False, index=True
    )
    arquivo: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)


class Marca(Base):
    __tablename__ = "marcas"
    __table_args__ = (
        UniqueConstraint("usuario_id", "cliente_id"),
        {"schema": "content"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    cliente_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True, index=True)
    paleta: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    tipografia: Mapped[str] = mapped_column(String(120), nullable=False)
    diretrizes_visuais: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    logo: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    logo_mime: Mapped[str | None] = mapped_column(String(50), nullable=True)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    logos: Mapped[list["LogoMarca"]] = relationship(cascade="all, delete-orphan", lazy="selectin")


class ArsenalCopy(Base):
    __tablename__ = "arsenais_copy"
    __table_args__ = (
        UniqueConstraint("usuario_id", "cliente_id"),
        {"schema": "content"},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    cliente_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    informacoes: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    manual_ia: Mapped[str | None] = mapped_column(Text, nullable=True)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class LogoMarca(Base):
    __tablename__ = "logos_marca"
    __table_args__ = {"schema": "content"}

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    marca_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("content.marcas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    arquivo: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    mime: Mapped[str] = mapped_column(String(50), nullable=False)
