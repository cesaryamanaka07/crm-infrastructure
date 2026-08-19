"""fluxos e contatos
Revision ID: 20260815_automation_01
Revises:
"""
from alembic import op
import sqlalchemy as sa
revision = "20260815_automation_01"; down_revision = None; branch_labels = None; depends_on = None
def upgrade():
    op.create_table("fluxos", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("cliente_id", sa.Uuid(), nullable=False), sa.Column("canal", sa.String(20), nullable=False),
        sa.Column("nome", sa.String(255), nullable=False), sa.Column("status", sa.String(20), nullable=False),
        sa.Column("blocos", sa.JSON(), nullable=False), sa.Column("conexoes", sa.JSON(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True)), sa.Column("atualizado_em", sa.DateTime(timezone=True)), schema="automation")
    op.create_index("ix_automation_fluxos_usuario_id", "fluxos", ["usuario_id"], schema="automation")
    op.create_index("ix_automation_fluxos_cliente_id", "fluxos", ["cliente_id"], schema="automation")
    op.create_index("ix_automation_fluxos_canal", "fluxos", ["canal"], schema="automation")
    op.create_table("contatos", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("cliente_id", sa.Uuid(), nullable=False), sa.Column("canal", sa.String(20), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=False), sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("telefone", sa.String(40)), sa.Column("respostas", sa.JSON(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True)), schema="automation")
    op.create_index("ix_automation_contatos_usuario_id", "contatos", ["usuario_id"], schema="automation")
    op.create_index("ix_automation_contatos_cliente_id", "contatos", ["cliente_id"], schema="automation")
def downgrade():
    op.drop_table("contatos", schema="automation"); op.drop_table("fluxos", schema="automation")
