import jwt
from datetime import datetime, timedelta, timezone
from pwdlib import PasswordHash
import os
from fastapi.security import HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException, status
from dotenv import load_dotenv
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.security import HTTPBearer
from app.core.database import get_session
from app.models.user import User

security = HTTPBearer()

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY") 
ALGORITHM = os.getenv("ALGORITHM")

ACCESS_TOKEN_EXPIRE_MINUTES = 30 # Token curto (acesso rápido)
REFRESH_TOKEN_EXPIRE_DAYS = 7 # Token longo (para não deslogar toda hora)
ACTIVATION_TOKEN_EXPIRE_HOURS = 24  # Token de ativação de conta

pwd_context = PasswordHash.recommended()

# --- Funções de Senha ---
def get_password_hash(password: str) -> str:
    """Recebe a senha pura e retorna o hash para salvar no banco."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """ Compara a senha informada com o hash salvo no banco."""
    return pwd_context.verify(plain_password, hashed_password)

# --- Funções de Token ---
def create_access_token(subject: str | int) -> str:
    """ Cria o token de acesso (curta duração). Subject é o ID ou email do usuário"""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "access"
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: str | int) -> str:
    """Cria o token de refresh (longa duração)."""
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "refresh"
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_activation_token(email: str) -> str:
    """Cria um token JWT específico para ativação de conta via e-mail."""
    expire = datetime.now(timezone.utc) + timedelta(hours=ACTIVATION_TOKEN_EXPIRE_HOURS)
    to_encode = {
        "sub": email,
        "exp": expire,
        "type": "activation" 
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    """Decodifica e valida a assinatura do token.
    Retorna o payload (dict) ou lança exceção se inválido."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None  # Token expirado
    except jwt.InvalidTokenError:
        return None  # Token malformado ou assinatura errada
    
async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session)
):
    
    # 1. Decodifica o Token
    payload = decode_token(token.credentials) 
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 2. Valida se é um Access Token (Refresh não pode logar em rotas)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido para acesso (tipo incorreto)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    
    # 3. Busca o usuário no banco
    user = await session.get(User, int(user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return user

class RoleChecker:
    """Dependência que verifica se o usuário autenticado possui um dos perfis permitidos.
    Uso: Depends(RoleChecker(["Gestor", "Professor"]))"""
    
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    async def __call__(self, user: User = Depends(get_current_user)) -> User:
        """Executado pelo FastAPI. Recebe o usuário validado por get_current_user."""
        
        if user.perfil not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para realizar esta ação (Acesso negado).",
            )
        
        return user