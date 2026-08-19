from datetime import datetime, timezone

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
    """Cria um JWT persistente, sem expiração automática.

    A sessão permanece válida enquanto o token existir no navegador. O logout
    remove o token do frontend e, portanto, exige um novo login nesse cliente.
    """
    dados_para_codificar = dados.copy()
    # Não incluímos ``exp``: a sessão não expira por tempo de uso.
    return jwt.encode(dados_para_codificar, settings.secret_key, algorithm=settings.algorithm)


def validar_token(token: str) -> dict | None:
    """Verifica a assinatura do token e retorna seus dados ou None."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except jwt.JWTError:
        return None
