import os


os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "segredo-de-teste-com-tamanho-suficiente")
os.environ.setdefault("CORS_ORIGINS", "origem-de-teste")
os.environ.setdefault("OMNIROUTE_BASE_URL", "https://omniroute.test/v1")
