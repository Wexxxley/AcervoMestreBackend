from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_session
from app.core.mail import send_reset_password_email
from app.models.user import User
from app.dtos.authDtos import ForgotPasswordRequest, LoginRequest, ResetPasswordRequest, TokenResponse, RefreshTokenRequest, ActivateAccountRequest
from app.core.security import (
    create_reset_password_token,
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
    """Autentica um usuário e retorna tokens de acesso e refresh.

    Parâmetros:
    - `credentials` (LoginRequest): Email e senha do usuário.

    Retorna:
    - `TokenResponse`: Access Token (30 minutos) e Refresh Token (7 dias).

    Erros possíveis:
    - 401: E-mail ou senha incorretos.
    - 403: Usuário inativo ou pendente de ativação.

    Permissões:
    - Público (Qualquer usuário).
    """
    
    # 1. Busca o usuário pelo e-mail
    statement = select(User).where(User.email == credentials.email)
    result = await session.exec(statement)
    user = result.first()

    # 2. Validações
    if not user or not user.senha_hash or not verify_password(credentials.password, user.senha_hash):
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
    """Gera um novo Access Token usando um Refresh Token válido.

    Parâmetros:
    - `request` (RefreshTokenRequest): O refresh token atual.

    Retorna:
    - `TokenResponse`: Novo Access Token e o Refresh Token original (ou rotacionado).

    Erros possíveis:
    - 401: Token inválido, expirado, ou tipo incorreto.
    - 401: Usuário associado ao token não encontrado ou inativo.

    Permissões:
    - Público (Validado pelo token).
    """
    
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
async def activate_account(body: ActivateAccountRequest, session: AsyncSession = Depends(get_session)):  
    """Ativa a conta de um usuário e define a senha inicial.

    Parâmetros:
    - `body` (ActivateAccountRequest): Token de ativação e nova senha.

    Retorna:
    - Mensagem de sucesso.

    Erros possíveis:
    - 400: Token inválido, expirado ou usuário já ativo.
    - 404: Usuário não encontrado.

    Permissões:
    - Público (Validado pelo token de ativação).
    """
    
    # 1. Decodificar Token
    payload = decode_token(body.token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido ou expirado."
        )

    # 2. Validar Tipo do Token
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

    # 4. Verificar se já não está ativo
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

@auth_router.post("/forgot_password", status_code=status.HTTP_200_OK)
async def forgot_password(
    body: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session)
):
    """Solicita um link para redefinição de senha.

    Parâmetros:
    - E-mail do usuário.

    Retorna:
    - Mensagem genérica de confirmação.

    Comportamento:
    - Verifica se o e-mail existe e se o usuário está ativo.
    - Se existir, gera um token e agenda o envio do e-mail em background.

    Permissões:
    - Público.
    """
    
    statement = select(User).where(User.email == body.email)
    result = await session.exec(statement)
    user = result.first()

    # Só envia se o usuário existir e estiver ativo
    if user and user.status == Status.Ativo:
        token = create_reset_password_token(user.email)
        
        # Agenda o envio do e-mail
        background_tasks.add_task(send_reset_password_email, user.email, token)

    return {"message": "Se o e-mail estiver cadastrado, você receberá um link para redefinir sua senha."}

@auth_router.post("/reset_password", status_code=status.HTTP_200_OK)
async def reset_password(
    body: ResetPasswordRequest, 
    session: AsyncSession = Depends(get_session)
):
    """Redefine a senha do usuário utilizando um token.

    Parâmetros:
    - `body` (ResetPasswordRequest): Token de reset e a nova senha.

    Retorna:
    - Mensagem de sucesso.

    Erros possíveis:
    - 400: Token inválido, expirado ou tipo incorreto.
    - 404: Usuário associado ao token não encontrado.

    Permissões:
    - Público (Validado pelo token de reset).
    """
    
    payload = decode_token(body.token)    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido ou expirado."
        )

    # Verifica se o token é do tipo reset_password
    if payload.get("type") != "reset_password":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido para esta operação."
        )

    email = payload.get("sub")

    statement = select(User).where(User.email == email)
    result = await session.exec(statement)
    user = result.first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Usuário associado ao token não encontrado."
        )

    user.senha_hash = get_password_hash(body.new_password)
    
    session.add(user)
    await session.commit()
    
    return {"message": "Senha alterada com sucesso! Você já pode fazer login com a nova senha."}