from uuid import UUID
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from app.config import settings

scheme = HTTPBearer(auto_error=False)


def obter_usuario_id(cred: HTTPAuthorizationCredentials | None = Depends(scheme)) -> UUID:
    erro = HTTPException(401, "Token inválido ou expirado")
    if not cred:
        raise erro
    try:
        return UUID(jwt.decode(cred.credentials, settings.secret_key, algorithms=[settings.algorithm])["sub"])
    except (JWTError, KeyError, ValueError, TypeError):
        raise erro

