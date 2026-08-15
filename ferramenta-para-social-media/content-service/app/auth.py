from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import settings


token_scheme = HTTPBearer(auto_error=False)


def obter_usuario_id(
    credenciais: HTTPAuthorizationCredentials | None = Depends(token_scheme),
) -> UUID:
    """Valida o JWT emitido pelo auth-service e retorna o usuário do token."""
    erro_token = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credenciais is None:
        raise erro_token

    try:
        payload = jwt.decode(
            credenciais.credentials,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        usuario_id = UUID(payload["sub"])
    except (JWTError, KeyError, TypeError, ValueError):
        raise erro_token

    return usuario_id
