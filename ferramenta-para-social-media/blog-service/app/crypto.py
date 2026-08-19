import base64
import hashlib
from cryptography.fernet import Fernet
from app.config import settings

_fernet = Fernet(base64.urlsafe_b64encode(hashlib.sha256(settings.secret_key.encode()).digest()))


def criptografar(valor: str | None):
    return _fernet.encrypt(valor.encode()) if valor else None


def descriptografar(valor: bytes | None):
    return _fernet.decrypt(valor).decode() if valor else None

