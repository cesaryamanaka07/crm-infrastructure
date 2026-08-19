from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool, text
from app.config import settings
from app.database import Base
from app import models  # noqa
config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)
if config.config_file_name: fileConfig(config.config_file_name)
target_metadata = Base.metadata
def run_migrations_online():
    connectable = engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS automation")); connection.commit()
        context.configure(connection=connection, target_metadata=target_metadata, include_schemas=True, version_table_schema="automation")
        with context.begin_transaction(): context.run_migrations()
run_migrations_online()
