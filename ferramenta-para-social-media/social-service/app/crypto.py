import base64
import hashlib

from cryptography.fernet import Fernet

from app.config import settings


_key = base64.urlsafe_b64encode(hashlib.sha256(settings.secret_key.encode()).digest())
_fernet = Fernet(_key)


def criptografar(valor: str | None) -> bytes | None:
    return _fernet.encrypt(valor.encode()) if valor else None


def descriptografar(valor: bytes | None) -> str | None:
    return _fernet.decrypt(valor).decode() if valor else None
