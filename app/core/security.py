from pwdlib import PasswordHash
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.user import User
from app.core.database import get_session
from app.enums.perfil import Perfil

pwd_context = PasswordHash.recommended()

def get_password_hash(password: str) -> str:
    """Recebe a senha pura e retorna o hash para salvar no banco."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compara a senha informada no login com o hash salvo no banco.
    Retorna True se forem compatíveis.
    """
    return pwd_context.verify(plain_password, hashed_password)

# TODO: Implementar autenticação JWT real
# Por enquanto, retorna um usuário mock para testes
async def get_current_user(
    session: AsyncSession = Depends(get_session)
) -> User | None:
    """
    Função placeholder para obter usuário atual.
    TODO: Implementar autenticação JWT real
    
    MODO DE TESTE: Retorna o primeiro usuário Professor do banco.
    Para habilitar modo sem autenticação (apenas recursos públicos), 
    altere para 'return None'.
    """
    # OPÇÃO 1: Retornar None (modo sem autenticação - apenas recursos públicos)
    # return None
    
    # OPÇÃO 2: Retornar usuário mock para testes (permite criar/editar/deletar)
    statement = select(User).where(User.perfil == Perfil.Professor).limit(1)
    result = await session.exec(statement)
    user = result.first()
    
    if user:
        return user
    
    # Se não encontrar Professor, tenta Coordenador
    statement = select(User).where(User.perfil == Perfil.Coordenador).limit(1)
    result = await session.exec(statement)
    return result.first()