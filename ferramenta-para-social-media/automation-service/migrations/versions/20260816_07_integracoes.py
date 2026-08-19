"""configuracoes de integracoes por cliente

Revision ID: 20260816_automation_07
Revises: 20260815_automation_06
"""
from alembic import op
import sqlalchemy as sa

revision = "20260816_automation_07"
down_revision = "20260815_automation_06"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "configuracoes",
        sa.Column("integracoes", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        schema="automation",
    )


def downgrade():
    op.drop_column("configuracoes", "integracoes", schema="automation")
