"""Adiciona narrativa estratégica e linha editorial por cliente."""
from alembic import op
import sqlalchemy as sa
revision = "20260815_10"
down_revision = "20260815_09"
branch_labels = None
depends_on = None

def upgrade():
    for tabela in ("narrativas_estrategicas", "linhas_editoriais"):
        op.create_table(tabela, sa.Column("id", sa.Uuid(), nullable=False), sa.Column("usuario_id", sa.Uuid(), nullable=False), sa.Column("cliente_id", sa.Uuid(), nullable=False), sa.Column("resultado", sa.JSON(), nullable=False), sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("usuario_id", "cliente_id"), schema="content")
        op.create_index(f"ix_content_{tabela}_usuario_id", tabela, ["usuario_id"], schema="content")
        op.create_index(f"ix_content_{tabela}_cliente_id", tabela, ["cliente_id"], schema="content")

def downgrade():
    op.drop_table("linhas_editoriais", schema="content")
    op.drop_table("narrativas_estrategicas", schema="content")
