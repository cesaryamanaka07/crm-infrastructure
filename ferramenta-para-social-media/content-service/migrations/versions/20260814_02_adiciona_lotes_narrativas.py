"""Adiciona quantidades, narrativas e especificação da legenda."""

from alembic import op


revision = "20260814_02"
down_revision = "20260814_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE content.conteudos "
        "ADD COLUMN IF NOT EXISTS quantidades JSONB"
    )
    op.execute(
        """
        UPDATE content.conteudos
        SET quantidades = jsonb_build_object(
            'post_unico', CASE WHEN formato = 'post_unico' THEN 1 ELSE 0 END,
            'carrossel', CASE WHEN formato = 'carrossel' THEN 1 ELSE 0 END,
            'reels', CASE WHEN formato = 'reels' THEN 1 ELSE 0 END,
            'story', CASE WHEN formato = 'story' THEN 1 ELSE 0 END
        )
        WHERE quantidades IS NULL
        """
    )
    op.execute(
        "ALTER TABLE content.conteudos ALTER COLUMN quantidades SET NOT NULL"
    )
    op.execute(
        "ALTER TABLE content.conteudos ALTER COLUMN quantidades "
        "SET DEFAULT '{\"post_unico\": 0, \"carrossel\": 0, \"reels\": 0, \"story\": 0}'::jsonb"
    )

    op.execute(
        "ALTER TABLE content.conteudos "
        "ADD COLUMN IF NOT EXISTS narrativas JSONB"
    )
    op.execute(
        """
        UPDATE content.conteudos
        SET narrativas = '{
            "post_unico": "Conversacional",
            "carrossel": "Conversacional",
            "reels": "Conversacional",
            "story": "Conversacional",
            "legenda": "Conversacional"
        }'::jsonb
        WHERE narrativas IS NULL
        """
    )
    op.execute(
        "ALTER TABLE content.conteudos ALTER COLUMN narrativas SET NOT NULL"
    )
    op.execute(
        "ALTER TABLE content.conteudos ALTER COLUMN narrativas "
        "SET DEFAULT '{}'::jsonb"
    )

    op.execute(
        "ALTER TABLE content.conteudos "
        "ADD COLUMN IF NOT EXISTS tamanho_legenda VARCHAR(20)"
    )
    op.execute(
        "UPDATE content.conteudos SET tamanho_legenda = 'media' "
        "WHERE tamanho_legenda IS NULL"
    )
    op.execute(
        "ALTER TABLE content.conteudos ALTER COLUMN tamanho_legenda SET NOT NULL"
    )
    op.execute(
        "ALTER TABLE content.conteudos ALTER COLUMN tamanho_legenda "
        "SET DEFAULT 'media'"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE content.conteudos DROP COLUMN IF EXISTS tamanho_legenda"
    )
    op.execute("ALTER TABLE content.conteudos DROP COLUMN IF EXISTS narrativas")
    op.execute("ALTER TABLE content.conteudos DROP COLUMN IF EXISTS quantidades")
