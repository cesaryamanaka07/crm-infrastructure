"""Google OAuth central por cliente."""
from alembic import op
import sqlalchemy as sa
revision = "20260816_social_06"; down_revision = "20260815_social_05"; branch_labels = None; depends_on = None
def upgrade():
    op.create_table("google_conexoes", sa.Column("id",sa.Uuid(),primary_key=True), sa.Column("usuario_id",sa.Uuid(),nullable=False),
      sa.Column("cliente_id",sa.Uuid(),nullable=False), sa.Column("email",sa.String(320),nullable=False),
      sa.Column("access_token",sa.LargeBinary(),nullable=False), sa.Column("refresh_token",sa.LargeBinary(),nullable=False),
      sa.Column("expira_em",sa.DateTime(timezone=True)), sa.Column("atualizado_em",sa.DateTime(timezone=True)),
      sa.ForeignKeyConstraint(["cliente_id"],["social.clientes.id"],ondelete="CASCADE"), sa.UniqueConstraint("usuario_id","cliente_id"), schema="social")
    op.create_index("ix_social_google_usuario","google_conexoes",["usuario_id"],schema="social")
    op.create_index("ix_social_google_cliente","google_conexoes",["cliente_id"],schema="social")
def downgrade(): op.drop_table("google_conexoes",schema="social")
