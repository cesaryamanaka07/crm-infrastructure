from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.config import settings

# Contexto do passlib configurado para usar bcrypt, o algoritmo de hash de senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def gerar_hash_senha(senha: str) -> str:
    """Transforma uma senha em texto puro num hash seguro para guardar no banco."""
    return pwd_context.hash(senha)


def verificar_senha(senha_texto_puro: str, senha_hash: str) -> bool:
    """Compara a senha digitada com o hash guardado. Retorna True se baterem."""
    return pwd_context.verify(senha_texto_puro, senha_hash)


def criar_token_acesso(dados: dict) -> str:
    """Cria um token JWT assinado, contendo os dados informados e uma data de expiração."""
    dados_para_codificar = dados.copy()
    expira_em = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    dados_para_codificar.update({"exp": expira_em})
    token = jwt.encode(dados_para_codificar, settings.secret_key, algorithm=settings.algorithm)
    return token


def validar_token(token: str) -> dict | None:
    """Verifica se um token é válido e não expirou. Retorna os dados dele ou None."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except jwt.JWTError:
        return None