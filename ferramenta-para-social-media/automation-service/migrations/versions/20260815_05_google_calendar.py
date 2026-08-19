"""integracao google calendar por cliente

Revision ID: 20260815_automation_05
Revises: 20260815_automation_04
"""
from alembic import op
import sqlalchemy as sa

revision = "20260815_automation_05"
down_revision = "20260815_automation_04"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("configuracoes", sa.Column("google_calendar_id", sa.String(320)), schema="automation")
    op.add_column("atividades", sa.Column("fim_em", sa.DateTime(timezone=True)), schema="automation")
    op.add_column("atividades", sa.Column("google_event_id", sa.String(255)), schema="automation")
    op.create_index("ix_automation_atividades_google_event_id", "atividades", ["google_event_id"], schema="automation")


def downgrade():
    op.drop_index("ix_automation_atividades_google_event_id", table_name="atividades", schema="automation")
    op.drop_column("atividades", "google_event_id", schema="automation")
    op.drop_column("atividades", "fim_em", schema="automation")
    op.drop_column("configuracoes", "google_calendar_id", schema="automation")

