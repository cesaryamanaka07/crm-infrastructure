"""Adiciona diretrizes visuais permanentes às marcas."""

from alembic import op
import sqlalchemy as sa


revision = "20260815_08"
down_revision = "20260815_07"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "marcas",
        sa.Column("diretrizes_visuais", sa.JSON(), nullable=False, server_default="{}"),
        schema="content",
    )
    op.alter_column("marcas", "diretrizes_visuais", server_default=None, schema="content")


def downgrade():
    op.drop_column("marcas", "diretrizes_visuais", schema="content")
