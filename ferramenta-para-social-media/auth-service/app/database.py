from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

# O "engine" é o que sabe como falar com o PostgreSQL de fato
engine = create_engine(settings.database_url)

# SessionLocal é uma "fábrica" de conversas com o banco.
# Cada requisição na API vai abrir uma sessão, usar e fechar.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base é a classe da qual todos os nossos modelos de tabela vão herdar
Base = declarative_base()


# Essa função entrega uma sessão de banco para cada requisição,
# e garante que ela é fechada no final, mesmo se der erro.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()