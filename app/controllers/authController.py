from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_session
from app.models.user import User
from app.dtos.authDtos import LoginRequest, TokenResponse, RefreshTokenRequest, ActivateAccountRequest
from app.core.security import (
    get_password_hash,
    verify_password, 
    create_access_token, 
    create_refresh_token, 
    decode_token
)
from app.enums.status import Status

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

@auth_router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest, session: AsyncSession = Depends(get_session)):
    
    # 1. Busca o usuário pelo e-mail
    statement = select(User).where(User.email == credentials.email)
    result = await session.exec(statement)
    user = result.first()

    # 2. Validações
    if not user or not verify_password(credentials.password, user.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Verifica se o usuário está ativo
    if user.status != Status.Ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo ou pendente de ativação."
        )

    # 4. Gera os tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )

@auth_router.post("/refresh_token", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest, session: AsyncSession = Depends(get_session)):
    
    # 1. Decodifica o Refresh Token recebido
    payload = decode_token(request.refresh_token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou expirado"
        )

    # 2. Garante que é um token do tipo 'refresh'
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido (esperado tipo refresh)"
        )

    user_id = payload.get("sub")

    # 3. Verifica no banco se o usuário ainda existe e está ativo
    statement = select(User).where(User.id == int(user_id))
    result = await session.exec(statement)
    user = result.first()

    if not user or user.status != Status.Ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou inativo"
        )

    # 4. Gera um novo Access Token
    new_access_token = create_access_token(user.id)
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=request.refresh_token 
    )
    
@auth_router.post("/activate_account", status_code=status.HTTP_200_OK)
async def activate_account(
    body: ActivateAccountRequest, 
    session: AsyncSession = Depends(get_session)
):
    """Recebe o token do e-mail e a nova senha.
    Valida o token, atualiza a senha e muda o status para Ativo."""
    
    # 1. Decodificar Token
    payload = decode_token(body.token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido ou expirado."
        )

    # 2. Validar Tipo do Token
    # Impede que alguém use um Access Token roubado para mudar a senha
    if payload.get("type") != "activation":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido (tipo incorreto)."
        )

    email = payload.get("sub")

    # 3. Buscar Usuário
    statement = select(User).where(User.email == email)
    result = await session.exec(statement)
    user = result.first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    # 4. Verificar se já não está ativo (Evitar reuso de link antigo)
    if user.status == Status.Ativo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta conta já foi ativada. Faça login normalmente."
        )

    # 5. Atualizar Dados
    user.senha_hash = get_password_hash(body.new_password)
    user.status = Status.Ativo
    
    session.add(user)
    await session.commit()
    
    return {"message": "Conta ativada com sucesso! Você já pode fazer login."}