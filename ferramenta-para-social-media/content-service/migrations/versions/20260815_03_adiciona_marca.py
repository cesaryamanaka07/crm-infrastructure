"""Adiciona identidade visual da marca por usuário."""

from alembic import op
import sqlalchemy as sa


revision = "20260815_03"
down_revision = "20260814_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "marcas",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("paleta", sa.JSON(), nullable=False),
        sa.Column("tipografia", sa.String(length=120), nullable=False),
        sa.Column("logo", sa.LargeBinary(), nullable=True),
        sa.Column("logo_mime", sa.String(length=50), nullable=True),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("usuario_id"),
        schema="content",
    )
    op.create_index(
        "ix_content_marcas_usuario_id",
        "marcas",
        ["usuario_id"],
        unique=True,
        schema="content",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_content_marcas_usuario_id", table_name="marcas", schema="content"
    )
    op.drop_table("marcas", schema="content")
