"""oauth google calendar e convidados

Revision ID: 20260815_automation_06
Revises: 20260815_automation_05
"""
from alembic import op
import sqlalchemy as sa

revision = "20260815_automation_06"
down_revision = "20260815_automation_05"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("configuracoes", sa.Column("google_email", sa.String(320)), schema="automation")
    op.add_column("configuracoes", sa.Column("google_access_token", sa.LargeBinary()), schema="automation")
    op.add_column("configuracoes", sa.Column("google_refresh_token", sa.LargeBinary()), schema="automation")
    op.add_column("configuracoes", sa.Column("google_token_expira_em", sa.DateTime(timezone=True)), schema="automation")
    op.add_column("atividades", sa.Column("convidados", sa.JSON(), nullable=False, server_default="[]"), schema="automation")
    op.alter_column("atividades", "convidados", server_default=None, schema="automation")

def downgrade():
    op.drop_column("atividades", "convidados", schema="automation")
    op.drop_column("configuracoes", "google_token_expira_em", schema="automation")
    op.drop_column("configuracoes", "google_refresh_token", schema="automation")
    op.drop_column("configuracoes", "google_access_token", schema="automation")
    op.drop_column("configuracoes", "google_email", schema="automation")
