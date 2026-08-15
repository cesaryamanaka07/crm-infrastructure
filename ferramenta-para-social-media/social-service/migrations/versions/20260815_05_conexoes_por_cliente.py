"""Vincula estados OAuth e conexões sociais aos clientes."""

from alembic import op
import sqlalchemy as sa


revision = "20260815_social_05"
down_revision = "20260815_social_04"
branch_labels = None
depends_on = None


def upgrade():
    for tabela in ("oauth_states", "conexoes"):
        op.add_column(tabela, sa.Column("cliente_id", sa.Uuid(), nullable=True), schema="social")
        op.create_foreign_key(
            f"fk_social_{tabela}_cliente_id",
            tabela,
            "clientes",
            ["cliente_id"],
            ["id"],
            source_schema="social",
            referent_schema="social",
            ondelete="CASCADE",
        )
        op.create_index(
            f"ix_social_{tabela}_cliente_id", tabela, ["cliente_id"], schema="social"
        )


def downgrade():
    for tabela in ("conexoes", "oauth_states"):
        op.drop_constraint(
            f"fk_social_{tabela}_cliente_id", tabela, schema="social", type_="foreignkey"
        )
        op.drop_index(f"ix_social_{tabela}_cliente_id", table_name=tabela, schema="social")
        op.drop_column(tabela, "cliente_id", schema="social")
