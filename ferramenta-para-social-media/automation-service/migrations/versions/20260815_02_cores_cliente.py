"""cores por cliente
Revision ID: 20260815_automation_02
Revises: 20260815_automation_01
"""
from alembic import op
import sqlalchemy as sa
revision = "20260815_automation_02"; down_revision = "20260815_automation_01"; branch_labels = None; depends_on = None
def upgrade():
    op.create_table("configuracoes", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("cliente_id", sa.Uuid(), nullable=False), sa.Column("cores", sa.JSON(), nullable=False),
        sa.UniqueConstraint("usuario_id", "cliente_id"), schema="automation")
    op.create_index("ix_automation_configuracoes_usuario_id", "configuracoes", ["usuario_id"], schema="automation")
    op.create_index("ix_automation_configuracoes_cliente_id", "configuracoes", ["cliente_id"], schema="automation")
def downgrade():
    op.drop_table("configuracoes", schema="automation")
