"""Adiciona hashtags padrão por marca e por conteúdo."""

from alembic import op
import sqlalchemy as sa


revision = "20260816_08"
down_revision = "20260815_11"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "marcas",
        sa.Column("hashtags_padrao", sa.JSON(), nullable=False, server_default="[]"),
        schema="content",
    )
    op.add_column(
        "conteudos",
        sa.Column("hashtags_padrao", sa.JSON(), nullable=False, server_default="[]"),
        schema="content",
    )
    op.alter_column("marcas", "hashtags_padrao", server_default=None, schema="content")
    op.alter_column("conteudos", "hashtags_padrao", server_default=None, schema="content")


def downgrade():
    op.drop_column("conteudos", "hashtags_padrao", schema="content")
    op.drop_column("marcas", "hashtags_padrao", schema="content")
