"""Cria estados OAuth e conexões sociais."""
from alembic import op
import sqlalchemy as sa

revision = "20260815_social_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("oauth_states",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("state_hash", sa.String(64), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False), sa.Column("provider", sa.String(30), nullable=False),
        sa.Column("expira_em", sa.DateTime(timezone=True), nullable=False), sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("state_hash"), schema="social")
    op.create_index("ix_social_oauth_states_usuario_id", "oauth_states", ["usuario_id"], schema="social")
    op.create_table("conexoes",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(30), nullable=False), sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("nome", sa.String(255), nullable=False), sa.Column("access_token", sa.LargeBinary(), nullable=False),
        sa.Column("refresh_token", sa.LargeBinary(), nullable=True), sa.Column("scopes", sa.Text(), nullable=False),
        sa.Column("expira_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("conectado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False), sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("usuario_id", "provider", "external_id"), schema="social")
    op.create_index("ix_social_conexoes_usuario_id", "conexoes", ["usuario_id"], schema="social")


def downgrade():
    op.drop_table("conexoes", schema="social")
    op.drop_table("oauth_states", schema="social")
