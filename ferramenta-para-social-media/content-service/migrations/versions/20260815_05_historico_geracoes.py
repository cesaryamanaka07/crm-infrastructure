"""Armazena o histórico das gerações de texto."""

from alembic import op
import sqlalchemy as sa


revision = "20260815_05"
down_revision = "20260815_04"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "geracoes_texto",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conteudo_id", sa.Uuid(), nullable=False),
        sa.Column("modelo", sa.String(120), nullable=False),
        sa.Column("conteudos", sa.JSON(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["conteudo_id"], ["content.conteudos.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="content",
    )
    op.create_index(
        "ix_content_geracoes_texto_conteudo_id",
        "geracoes_texto",
        ["conteudo_id"],
        schema="content",
    )


def downgrade():
    op.drop_table("geracoes_texto", schema="content")
