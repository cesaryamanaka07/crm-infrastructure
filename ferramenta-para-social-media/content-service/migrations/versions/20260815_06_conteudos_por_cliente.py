"""Vincula briefings e gerações ao cliente selecionado."""

from alembic import op
import sqlalchemy as sa


revision = "20260815_06"
down_revision = "20260815_05"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "conteudos", sa.Column("cliente_id", sa.Uuid(), nullable=True), schema="content"
    )
    op.create_index(
        "ix_content_conteudos_cliente_id",
        "conteudos",
        ["cliente_id"],
        schema="content",
    )


def downgrade():
    op.drop_index(
        "ix_content_conteudos_cliente_id", table_name="conteudos", schema="content"
    )
    op.drop_column("conteudos", "cliente_id", schema="content")
