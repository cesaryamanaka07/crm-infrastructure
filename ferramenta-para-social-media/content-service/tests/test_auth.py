from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt

from app.auth import obter_usuario_id
from app.config import settings


def criar_credencial(payload: dict) -> HTTPAuthorizationCredentials:
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_retorna_usuario_do_token_valido():
    usuario_id = uuid4()
    credencial = criar_credencial(
        {
            "sub": str(usuario_id),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        }
    )

    assert obter_usuario_id(credencial) == usuario_id


@pytest.mark.parametrize(
    "credencial",
    [
        None,
        HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalido"),
    ],
)
def test_rejeita_token_ausente_ou_invalido(credencial):
    with pytest.raises(HTTPException) as erro:
        obter_usuario_id(credencial)

    assert erro.value.status_code == 401
