from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Usuario
from app.schemas import LoginRequest, TokenResponse, UsuarioResponse
from app.auth import verificar_senha, criar_token_acesso, validar_token

router = APIRouter()

# Esquema simples: espera um token "Bearer" puro no cabeçalho Authorization.
# Diferente do OAuth2PasswordBearer, não exige um formulário de login padrão,
# o que combina com nosso /login que recebe JSON (email + senha).
token_scheme = HTTPBearer()


@router.post("/login", response_model=TokenResponse)
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == dados.email).first()

    # Mensagem de erro genérica de propósito: não revelamos se foi o
    # e-mail ou a senha que estava errada (evita dar pistas a invasores)
    erro_credenciais = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="E-mail ou senha inválidos",
    )

    if not usuario:
        raise erro_credenciais

    if not verificar_senha(dados.senha, usuario.senha_hash):
        raise erro_credenciais

    if not usuario.ativo:
        raise HTTPException(status_code=403, detail="Usuário inativo")

    token = criar_token_acesso({"sub": str(usuario.id)})
    return TokenResponse(access_token=token)


def obter_usuario_atual(
    credenciais: HTTPAuthorizationCredentials = Depends(token_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    """Dependência usada por qualquer rota que exija login.
    Lê o token enviado, valida, e busca o usuário correspondente."""
    erro_token = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credenciais.credentials
    payload = validar_token(token)
    if payload is None:
        raise erro_token

    usuario_id = payload.get("sub")
    if usuario_id is None:
        raise erro_token

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if usuario is None:
        raise erro_token

    return usuario


@router.get("/me", response_model=UsuarioResponse)
def ler_usuario_logado(usuario_atual: Usuario = Depends(obter_usuario_atual)):
    """Rota simples para testar se o token está funcionando.
    Qualquer outro microserviço vai usar essa mesma lógica de validação."""
    return usuario_atual