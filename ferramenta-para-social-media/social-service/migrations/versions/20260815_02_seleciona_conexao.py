"""Adiciona seleção de conexão ativa por rede social."""

from alembic import op
import sqlalchemy as sa


revision = "20260815_social_02"
down_revision = "20260815_social_01"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "conexoes",
        sa.Column("selecionada", sa.Boolean(), nullable=False, server_default=sa.false()),
        schema="social",
    )
    op.execute("""
        WITH primeiras AS (
            SELECT id, ROW_NUMBER() OVER (
                PARTITION BY usuario_id, provider ORDER BY conectado_em, id
            ) AS ordem
            FROM social.conexoes
        )
        UPDATE social.conexoes AS conexao
        SET selecionada = TRUE
        FROM primeiras
        WHERE conexao.id = primeiras.id AND primeiras.ordem = 1
    """)
    op.alter_column("conexoes", "selecionada", server_default=None, schema="social")


def downgrade():
    op.drop_column("conexoes", "selecionada", schema="social")
