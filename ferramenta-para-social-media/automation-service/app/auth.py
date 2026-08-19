from uuid import UUID
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from app.config import settings

bearer = HTTPBearer()
def obter_usuario_id(credenciais: HTTPAuthorizationCredentials = Depends(bearer)) -> UUID:
    try:
        payload = jwt.decode(credenciais.credentials, settings.secret_key, algorithms=[settings.algorithm])
        return UUID(payload["sub"])
    except (JWTError, KeyError, ValueError) as erro:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado") from erro
