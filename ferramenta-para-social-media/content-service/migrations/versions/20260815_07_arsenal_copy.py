"""Adiciona Arsenal de Copy por cliente e seleção nos briefings."""

from alembic import op
import sqlalchemy as sa


revision = "20260815_07"
down_revision = "20260815_06"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "arsenais_copy",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("cliente_id", sa.Uuid(), nullable=False),
        sa.Column("informacoes", sa.JSON(), nullable=False),
        sa.Column("manual_ia", sa.Text(), nullable=True),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("usuario_id", "cliente_id"),
        schema="content",
    )
    op.create_index("ix_content_arsenais_copy_usuario_id", "arsenais_copy", ["usuario_id"], schema="content")
    op.create_index("ix_content_arsenais_copy_cliente_id", "arsenais_copy", ["cliente_id"], schema="content")
    op.add_column("conteudos", sa.Column("arsenal_campos", sa.JSON(), nullable=False, server_default="[]"), schema="content")
    op.add_column("conteudos", sa.Column("instrucoes_ia", sa.Text(), nullable=True), schema="content")
    op.alter_column("conteudos", "arsenal_campos", server_default=None, schema="content")


def downgrade():
    op.drop_column("conteudos", "instrucoes_ia", schema="content")
    op.drop_column("conteudos", "arsenal_campos", schema="content")
    op.drop_table("arsenais_copy", schema="content")
