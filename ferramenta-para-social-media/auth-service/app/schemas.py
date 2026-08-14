from uuid import UUID
from pydantic import BaseModel, EmailStr


# O que a API espera RECEBER no login
class LoginRequest(BaseModel):
    email: EmailStr
    senha: str


# O que a API DEVOLVE depois de um login bem-sucedido
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# O que a API devolve ao consultar dados do usuário logado
# (repare que NÃO existe campo de senha aqui — nunca devolvemos isso)
class UsuarioResponse(BaseModel):
    id: UUID
    nome: str
    email: EmailStr

    class Config:
        from_attributes = True  # permite converter direto do objeto do SQLAlchemy