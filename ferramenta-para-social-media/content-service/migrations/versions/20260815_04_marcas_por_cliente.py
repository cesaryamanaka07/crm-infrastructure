"""Separa marcas por cliente e permite múltiplos logotipos."""

from alembic import op
import sqlalchemy as sa


revision = "20260815_04"
down_revision = "20260815_03"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("marcas", sa.Column("cliente_id", sa.Uuid(), nullable=True), schema="content")
    op.drop_index("ix_content_marcas_usuario_id", table_name="marcas", schema="content")
    op.drop_constraint("marcas_usuario_id_key", "marcas", schema="content", type_="unique")
    op.create_index("ix_content_marcas_usuario_id", "marcas", ["usuario_id"], schema="content")
    op.create_index("ix_content_marcas_cliente_id", "marcas", ["cliente_id"], schema="content")
    op.create_unique_constraint("uq_content_marcas_usuario_cliente", "marcas", ["usuario_id", "cliente_id"], schema="content")
    op.create_table(
        "logos_marca",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("marca_id", sa.Uuid(), nullable=False),
        sa.Column("arquivo", sa.LargeBinary(), nullable=False),
        sa.Column("mime", sa.String(50), nullable=False),
        sa.ForeignKeyConstraint(["marca_id"], ["content.marcas.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="content",
    )
    op.create_index("ix_content_logos_marca_marca_id", "logos_marca", ["marca_id"], schema="content")
    op.execute("""
        INSERT INTO content.logos_marca (id, marca_id, arquivo, mime)
        SELECT gen_random_uuid(), id, logo, logo_mime
        FROM content.marcas WHERE logo IS NOT NULL AND logo_mime IS NOT NULL
    """)


def downgrade():
    op.drop_table("logos_marca", schema="content")
    op.drop_constraint("uq_content_marcas_usuario_cliente", "marcas", schema="content", type_="unique")
    op.drop_index("ix_content_marcas_cliente_id", table_name="marcas", schema="content")
    op.drop_index("ix_content_marcas_usuario_id", table_name="marcas", schema="content")
    op.create_index("ix_content_marcas_usuario_id", "marcas", ["usuario_id"], unique=True, schema="content")
    op.drop_column("marcas", "cliente_id", schema="content")
