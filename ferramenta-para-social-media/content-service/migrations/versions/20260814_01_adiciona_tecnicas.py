"""Adiciona catálogo de técnicas e relacionamento com conteúdos."""

import uuid

import sqlalchemy as sa
from alembic import op

from app.catalog import TECNICAS


revision = "20260814_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS content")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS content.conteudos (
            id UUID PRIMARY KEY,
            usuario_id UUID NOT NULL,
            intencao VARCHAR(500) NOT NULL,
            tema VARCHAR(300) NOT NULL,
            perspectiva VARCHAR(500) NOT NULL,
            modelo VARCHAR(80) NOT NULL,
            tom_de_voz VARCHAR(80) NOT NULL,
            formato VARCHAR(30) NOT NULL,
            observacoes TEXT,
            status VARCHAR(30) NOT NULL DEFAULT 'rascunho',
            criado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            atualizado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_content_conteudos_usuario_id "
        "ON content.conteudos (usuario_id)"
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS content.tecnicas (
            id UUID PRIMARY KEY,
            slug VARCHAR(50) UNIQUE NOT NULL,
            nome VARCHAR(100) NOT NULL
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS content.conteudo_tecnicas (
            conteudo_id UUID NOT NULL
                REFERENCES content.conteudos(id) ON DELETE CASCADE,
            tecnica_id UUID NOT NULL
                REFERENCES content.tecnicas(id) ON DELETE CASCADE,
            PRIMARY KEY (conteudo_id, tecnica_id)
        )
        """
    )

    connection = op.get_bind()
    for slug, nome in TECNICAS.items():
        tecnica_id = uuid.uuid5(uuid.NAMESPACE_URL, f"content-technique:{slug}")
        connection.execute(
            sa.text(
                """
                INSERT INTO content.tecnicas (id, slug, nome)
                VALUES (:id, :slug, :nome)
                ON CONFLICT (slug) DO UPDATE SET nome = EXCLUDED.nome
                """
            ),
            {"id": tecnica_id, "slug": slug, "nome": nome},
        )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS content.conteudo_tecnicas")
    op.execute("DROP TABLE IF EXISTS content.tecnicas")
