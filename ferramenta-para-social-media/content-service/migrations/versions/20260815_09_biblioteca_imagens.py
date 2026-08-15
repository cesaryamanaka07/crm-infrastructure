"""Armazena imagens criadas e as associa aos textos."""

from alembic import op
import sqlalchemy as sa

revision = "20260815_09"
down_revision = "20260815_08"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "geracoes_imagem",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("cliente_id", sa.Uuid(), nullable=False),
        sa.Column("geracao_texto_id", sa.Uuid(), nullable=True),
        sa.Column("conteudo_indice", sa.Integer(), nullable=True),
        sa.Column("formato", sa.String(30), nullable=False),
        sa.Column("tamanho", sa.String(20), nullable=False),
        sa.Column("modelo", sa.String(120), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["geracao_texto_id"], ["content.geracoes_texto.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"), schema="content",
    )
    for coluna in ("usuario_id", "cliente_id", "geracao_texto_id"):
        op.create_index(f"ix_content_geracoes_imagem_{coluna}", "geracoes_imagem", [coluna], schema="content")
    op.create_table(
        "imagens_salvas",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("geracao_imagem_id", sa.Uuid(), nullable=False),
        sa.Column("arquivo", sa.LargeBinary(), nullable=False),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.ForeignKeyConstraint(["geracao_imagem_id"], ["content.geracoes_imagem.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"), schema="content",
    )
    op.create_index("ix_content_imagens_salvas_geracao_imagem_id", "imagens_salvas", ["geracao_imagem_id"], schema="content")


def downgrade():
    op.drop_table("imagens_salvas", schema="content")
    op.drop_table("geracoes_imagem", schema="content")
