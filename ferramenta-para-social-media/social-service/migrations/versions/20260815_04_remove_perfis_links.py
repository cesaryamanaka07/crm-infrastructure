"""Remove perfis por link e métricas manuais, preservando clientes."""

from alembic import op
import sqlalchemy as sa


revision = "20260815_social_04"
down_revision = "20260815_social_03"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table("perfis_clientes", schema="social")


def downgrade():
    op.create_table(
        "perfis_clientes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("cliente_id", sa.Uuid(), nullable=False),
        sa.Column("tipo", sa.String(30), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("visualizacoes", sa.BigInteger(), nullable=False),
        sa.Column("visualizacoes_seguidores", sa.BigInteger(), nullable=False),
        sa.Column("visualizacoes_nao_seguidores", sa.BigInteger(), nullable=False),
        sa.Column("curtidas", sa.BigInteger(), nullable=False),
        sa.Column("seguidores", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(["cliente_id"], ["social.clientes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cliente_id", "tipo"),
        schema="social",
    )
    op.create_index("ix_social_perfis_clientes_cliente_id", "perfis_clientes", ["cliente_id"], schema="social")
