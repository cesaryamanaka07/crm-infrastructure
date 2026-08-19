"""crm, configuracoes e calendario
Revision ID: 20260815_automation_04
Revises: 20260815_automation_03
"""
from alembic import op
import sqlalchemy as sa

revision = "20260815_automation_04"
down_revision = "20260815_automation_03"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("contatos", sa.Column("sobrenome", sa.String(255), nullable=False, server_default=""), schema="automation")
    op.add_column("contatos", sa.Column("email", sa.String(255)), schema="automation")
    op.add_column("contatos", sa.Column("instagram_usuario", sa.String(255)), schema="automation")
    op.add_column("contatos", sa.Column("facebook_usuario", sa.String(255)), schema="automation")
    op.add_column("contatos", sa.Column("etapa_id", sa.String(100)), schema="automation")
    op.add_column("contatos", sa.Column("qualidade_id", sa.String(100)), schema="automation")
    op.add_column("contatos", sa.Column("tags", sa.JSON(), nullable=False, server_default="[]"), schema="automation")
    op.add_column("configuracoes", sa.Column("crm_config", sa.JSON(), nullable=False, server_default="{}"), schema="automation")
    op.create_table("atividades",
        sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("cliente_id", sa.Uuid(), nullable=False), sa.Column("contato_id", sa.Uuid()),
        sa.Column("tipo", sa.String(30), nullable=False), sa.Column("titulo", sa.String(255), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=False), sa.Column("inicio_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("concluida", sa.Boolean(), nullable=False), sa.Column("criado_em", sa.DateTime(timezone=True)), schema="automation")
    op.create_index("ix_automation_atividades_usuario_id", "atividades", ["usuario_id"], schema="automation")
    op.create_index("ix_automation_atividades_cliente_id", "atividades", ["cliente_id"], schema="automation")
    op.create_index("ix_automation_atividades_contato_id", "atividades", ["contato_id"], schema="automation")

def downgrade():
    op.drop_table("atividades", schema="automation")
    op.drop_column("configuracoes", "crm_config", schema="automation")
    for coluna in ["tags", "qualidade_id", "etapa_id", "facebook_usuario", "instagram_usuario", "email", "sobrenome"]:
        op.drop_column("contatos", coluna, schema="automation")
