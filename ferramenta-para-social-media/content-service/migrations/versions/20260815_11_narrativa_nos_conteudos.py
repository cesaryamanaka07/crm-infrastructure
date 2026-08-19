"""Permite aplicar a narrativa estratégica na criação de textos."""
from alembic import op
import sqlalchemy as sa
revision = "20260815_11"
down_revision = "20260815_10"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("conteudos", sa.Column("usar_narrativa", sa.Boolean(), nullable=False, server_default=sa.true()), schema="content")
    op.alter_column("conteudos", "usar_narrativa", server_default=None, schema="content")

def downgrade():
    op.drop_column("conteudos", "usar_narrativa", schema="content")
