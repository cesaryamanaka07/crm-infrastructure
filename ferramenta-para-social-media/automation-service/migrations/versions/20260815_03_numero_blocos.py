"""numero monotônico dos blocos
Revision ID: 20260815_automation_03
Revises: 20260815_automation_02
"""
from alembic import op
import sqlalchemy as sa
revision = "20260815_automation_03"; down_revision = "20260815_automation_02"; branch_labels = None; depends_on = None
def upgrade():
    op.add_column("fluxos", sa.Column("proximo_numero", sa.Integer(), nullable=False, server_default="1"), schema="automation")
def downgrade():
    op.drop_column("fluxos", "proximo_numero", schema="automation")
