import uuid
from datetime import datetime, timezone
from sqlalchemy import JSON, DateTime, ForeignKey, Integer, LargeBinary, String, Text, Uuid, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


def agora():
    return datetime.now(timezone.utc)


class IntegracaoBlog(Base):
    __tablename__ = "integracoes"
    __table_args__ = (UniqueConstraint("usuario_id", "cliente_id"), {"schema": "blog"})
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    cliente_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    wordpress_url: Mapped[str | None] = mapped_column(String(500))
    wordpress_usuario: Mapped[str | None] = mapped_column(String(200))
    wordpress_senha_app: Mapped[bytes | None] = mapped_column(LargeBinary)
    wordpress_status_padrao: Mapped[str] = mapped_column(String(20), default="draft")
    google_planilha_id: Mapped[str | None] = mapped_column(String(300))
    google_aba: Mapped[str] = mapped_column(String(100), default="Ideias de Blog")
    google_conta_servico: Mapped[bytes | None] = mapped_column(LargeBinary)
    google_email: Mapped[str | None] = mapped_column(String(320))
    google_access_token: Mapped[bytes | None] = mapped_column(LargeBinary)
    google_refresh_token: Mapped[bytes | None] = mapped_column(LargeBinary)
    google_token_expira_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora, onupdate=agora)


class IdeiaBlog(Base):
    __tablename__ = "ideias"
    __table_args__ = (UniqueConstraint("usuario_id", "cliente_id", "fingerprint"), {"schema": "blog"})
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    cliente_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    titulo: Mapped[str] = mapped_column(String(500))
    tema: Mapped[str] = mapped_column(String(500))
    palavra_chave: Mapped[str] = mapped_column(String(250))
    palavras_secundarias: Mapped[list] = mapped_column(JSON, default=list)
    intencao_busca: Mapped[str] = mapped_column(String(50), default="informacional")
    foco: Mapped[str | None] = mapped_column(Text)
    tamanho: Mapped[str] = mapped_column(String(30), default="1500_2500")
    gerar_imagens: Mapped[bool] = mapped_column(default=True)
    destino_wordpress: Mapped[str] = mapped_column(String(20), default="nenhum")
    status: Mapped[str] = mapped_column(String(30), default="ideia", index=True)
    agendado_para: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    fingerprint: Mapped[str] = mapped_column(String(64))
    origem: Mapped[str] = mapped_column(String(20), default="manual")
    google_linha: Mapped[str | None] = mapped_column(String(50))
    erro: Mapped[str | None] = mapped_column(Text)
    processado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)


class ArtigoBlog(Base):
    __tablename__ = "artigos"
    __table_args__ = {"schema": "blog"}
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    ideia_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("blog.ideias.id", ondelete="SET NULL"), unique=True)
    usuario_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    cliente_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    titulo: Mapped[str] = mapped_column(String(500))
    meta_titulo: Mapped[str] = mapped_column(String(200))
    meta_descricao: Mapped[str] = mapped_column(String(400))
    slug: Mapped[str] = mapped_column(String(500))
    resumo: Mapped[str] = mapped_column(Text)
    palavra_chave: Mapped[str] = mapped_column(String(250))
    palavras_secundarias: Mapped[list] = mapped_column(JSON, default=list)
    intencao_busca: Mapped[str] = mapped_column(String(50))
    conteudo_html: Mapped[str] = mapped_column(Text)
    estrutura: Mapped[list] = mapped_column(JSON, default=list)
    faq: Mapped[list] = mapped_column(JSON, default=list)
    imagens: Mapped[list] = mapped_column(JSON, default=list)
    checklist_seo: Mapped[dict] = mapped_column(JSON, default=dict)
    pontuacao_seo: Mapped[int] = mapped_column(Integer, default=0)
    total_palavras: Mapped[int] = mapped_column(Integer, default=0)
    modelo_ia: Mapped[str] = mapped_column(String(150))
    status: Mapped[str] = mapped_column(String(30), default="gerado", index=True)
    agendado_para: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    wordpress_post_id: Mapped[int | None] = mapped_column(Integer, unique=True)
    wordpress_url: Mapped[str | None] = mapped_column(String(700))
    publicado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora, onupdate=agora)
