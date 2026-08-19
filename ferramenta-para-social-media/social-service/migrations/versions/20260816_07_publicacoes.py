"""Publicações sociais, arquivos e agendamento."""
from alembic import op
import sqlalchemy as sa

revision = "20260816_social_07"
down_revision = "20260816_social_06"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "publicacoes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("cliente_id", sa.Uuid(), nullable=False),
        sa.Column("formato", sa.String(30), nullable=False),
        sa.Column("titulo", sa.String(500), nullable=False, server_default=""),
        sa.Column("legenda", sa.Text(), nullable=False, server_default=""),
        sa.Column("hashtags", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("roteiro", sa.Text()),
        sa.Column("duracao_segundos", sa.Integer()),
        sa.Column("status", sa.String(30), nullable=False, server_default="rascunho"),
        sa.Column("publicar_em", sa.DateTime(timezone=True)),
        sa.Column("criado_em", sa.DateTime(timezone=True)),
        sa.Column("atualizado_em", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["cliente_id"], ["social.clientes.id"], ondelete="CASCADE"),
        schema="social",
    )
    op.create_index("ix_social_publicacoes_usuario_id", "publicacoes", ["usuario_id"], schema="social")
    op.create_index("ix_social_publicacoes_cliente_id", "publicacoes", ["cliente_id"], schema="social")
    op.create_index("ix_social_publicacoes_status", "publicacoes", ["status"], schema="social")
    op.create_index("ix_social_publicacoes_publicar_em", "publicacoes", ["publicar_em"], schema="social")

    op.create_table(
        "publicacao_itens",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("publicacao_id", sa.Uuid(), nullable=False),
        sa.Column("ordem", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("titulo", sa.String(500), nullable=False, server_default=""),
        sa.Column("prompt", sa.Text(), nullable=False, server_default=""),
        sa.Column("arquivo", sa.LargeBinary(), nullable=False),
        sa.Column("nome_arquivo", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(120), nullable=False),
        sa.ForeignKeyConstraint(["publicacao_id"], ["social.publicacoes.id"], ondelete="CASCADE"),
        schema="social",
    )
    op.create_index("ix_social_publicacao_itens_publicacao_id", "publicacao_itens", ["publicacao_id"], schema="social")

    op.create_table(
        "publicacao_redes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("publicacao_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("conexao_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pendente"),
        sa.Column("external_id", sa.String(255)),
        sa.Column("erro", sa.Text()),
        sa.Column("publicado_em", sa.DateTime(timezone=True)),
        sa.Column("criado_em", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["publicacao_id"], ["social.publicacoes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["conexao_id"], ["social.conexoes.id"], ondelete="CASCADE"),
        schema="social",
    )
    op.create_index("ix_social_publicacao_redes_publicacao_id", "publicacao_redes", ["publicacao_id"], schema="social")
    op.create_index("ix_social_publicacao_redes_status", "publicacao_redes", ["status"], schema="social")

    op.create_table(
        "publicacao_ideias",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("publicacao_id", sa.Uuid(), nullable=False, unique=True),
        sa.Column("ideia_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("criado_em", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["publicacao_id"], ["social.publicacoes.id"], ondelete="CASCADE"),
        schema="social",
    )


def downgrade():
    op.drop_table("publicacao_ideias", schema="social")
    op.drop_table("publicacao_redes", schema="social")
    op.drop_table("publicacao_itens", schema="social")
    op.drop_table("publicacoes", schema="social")
