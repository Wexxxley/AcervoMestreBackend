import pytest
import jwt
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone, date 
from sqlmodel import select
from app.models.user import User
from app.enums.status import Status
from app.core.security import get_password_hash

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "secret_key_exemplo_para_testes") 
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# --- DADOS MOCK PARA TESTES ---
AUTH_PAYLOAD = {
    "email": "auth.teste@example.com",
    "password": "senha_forte_123"
}

@pytest.mark.asyncio
async def test_login_success(client, session):
    """Testa o fluxo feliz de login com credenciais corretas."""
    
    # 1. Cria usuário no banco
    hashed_password = get_password_hash(AUTH_PAYLOAD["password"])
    user = User(
        email=AUTH_PAYLOAD["email"],
        senha_hash=hashed_password,
        status=Status.Ativo,
        nome="Tester Auth",
        data_nascimento=date(2000, 1, 1),
        perfil="Gestor" 
    )
    session.add(user)
    await session.commit()

    # 2. Login
    response = await client.post("/auth/login", json=AUTH_PAYLOAD)

    # 3. Validações
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

@pytest.mark.asyncio
async def test_login_wrong_credentials(client, session):
    """Testa erro 401 ao errar a senha ou email."""
    
    hashed_password = get_password_hash(AUTH_PAYLOAD["password"])
    user = User(
        email=AUTH_PAYLOAD["email"],
        senha_hash=hashed_password,
        status=Status.Ativo,
        nome="Tester Fail",
        perfil="Gestor" 
    )
    session.add(user)
    await session.commit()

    # Senha errada
    payload_wrong_pass = AUTH_PAYLOAD.copy()
    payload_wrong_pass["password"] = "senha_errada"
    
    response = await client.post("/auth/login", json=payload_wrong_pass)
    assert response.status_code == 401
    assert "incorretos" in response.json()["detail"]

    # Email inexistente
    payload_wrong_email = AUTH_PAYLOAD.copy()
    payload_wrong_email["email"] = "inexistente@example.com"
    
    response_email = await client.post("/auth/login", json=payload_wrong_email)
    assert response_email.status_code == 401 

@pytest.mark.asyncio
async def test_login_inactive_user(client, session):
    """Testa bloqueio de login para usuário Inativo."""
    
    hashed_password = get_password_hash(AUTH_PAYLOAD["password"])
    user = User(
        email="inativo@example.com",
        senha_hash=hashed_password,
        status=Status.Inativo,
        nome="Tester Inativo",
        perfil="Gestor" 
    )
    session.add(user)
    await session.commit()

    payload = {"email": "inativo@example.com", "password": AUTH_PAYLOAD["password"]}
    response = await client.post("/auth/login", json=payload)

    assert response.status_code == 403
    assert "inativo" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_login_pending_user(client, session):
    """Testa bloqueio de login para usuário Aguardando Ativação."""
    
    user = User(
        email="pendente@example.com",
        senha_hash=None, 
        status=Status.AguardandoAtivacao,
        nome="Tester Pendente",
        perfil="Gestor"
    )
    session.add(user)
    await session.commit()

    payload = {"email": "pendente@example.com", "password": "qualquer_senha"}
    response = await client.post("/auth/login", json=payload)
    
    assert response.status_code in [401, 403]

@pytest.mark.asyncio
async def test_refresh_token_flow(client, session):
    """Testa a geração de um novo access token via refresh token."""
    
    hashed_password = get_password_hash(AUTH_PAYLOAD["password"])
    user = User(
        email=AUTH_PAYLOAD["email"],
        senha_hash=hashed_password,
        status=Status.Ativo,
        nome="Tester Refresh",
        perfil="Gestor" 
    )
    session.add(user)
    await session.commit()

    # Login para pegar tokens válidos
    login_res = await client.post("/auth/login", json=AUTH_PAYLOAD)
    refresh_token = login_res.json()["refresh_token"]

    # Refresh
    response = await client.post("/auth/refresh_token", json={"refresh_token": refresh_token})
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["access_token"] != refresh_token 

@pytest.mark.asyncio
async def test_activate_account_success(client, session):
    """Testa a ativação da conta via token."""
    
    email_target = "novo.convite@example.com"
    
    # 1. Cria usuário Pendente (sem senha)
    user = User(
        email=email_target,
        status=Status.AguardandoAtivacao,
        nome="Tester Convite",
        senha_hash=None,
        perfil="Professor"
    )
    session.add(user)
    await session.commit()

    # 2. Gera token manualmente
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode = {"exp": expire, "sub": email_target, "type": "activation"}
    
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    # 3. Chama endpoint
    new_password = "NovaSenhaForte!123"
    response = await client.post("/auth/activate_account", json={
        "token": token,
        "new_password": new_password
    })

    assert response.status_code == 200
    
    # 4. Verifica BD
    statement = select(User).where(User.email == email_target)
    result = await session.exec(statement)
    updated_user = result.first()
    
    assert updated_user.status == Status.Ativo
    assert updated_user.senha_hash is not None

@pytest.mark.asyncio
async def test_activate_account_invalid_token(client):
    """Testa erro com token inválido."""
    response = await client.post("/auth/activate_account", json={
        "token": "token.totalmente.invalido",
        "new_password": "123"
    })
    
    assert response.status_code in [400, 401]
    
@pytest.mark.asyncio
async def test_forgot_password_existing_user(client, session):
    """
    Testa solicitação de recuperação para usuário existente.
    Deve retornar 200 OK.
    """
    # 1. Arrange: Criar usuário ativo
    user = User(
        email="recover@example.com",
        senha_hash=get_password_hash("senha_antiga"),
        status=Status.Ativo,
        nome="Tester Recover",
        perfil="Professor",
        data_nascimento=date(1990, 5, 20)
    )
    session.add(user)
    await session.commit()

    # 2. Act
    response = await client.post("/auth/forgot_password", json={"email": "recover@example.com"})

    # 3. Assert
    assert response.status_code == 200
    assert "receberá um link" in response.json()["message"]

@pytest.mark.asyncio
async def test_forgot_password_non_existent_user(client):
    """
    Testa solicitação para e-mail que NÃO existe.
    Deve retornar 200 OK por segurança (para não revelar usuários cadastrados).
    """
    response = await client.post("/auth/forgot_password", json={"email": "fantasma@example.com"})

    assert response.status_code == 200
    assert "receberá um link" in response.json()["message"]

@pytest.mark.asyncio
async def test_reset_password_success(client, session):
    """
    Testa o fluxo completo de redefinição de senha com token válido.
    """
    email_target = "reset.pass@example.com"
    old_pass = "SenhaAntiga123"
    
    # 1. Arrange: Usuário com senha antiga
    user = User(
        email=email_target,
        senha_hash=get_password_hash(old_pass),
        status=Status.Ativo,
        nome="Tester Reset",
        perfil="Gestor",
        data_nascimento=date(1985, 10, 10)
    )
    session.add(user)
    await session.commit()

    # 2. Gerar Token de Reset Manualmente
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode = {"exp": expire, "sub": email_target, "type": "reset_password"}
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    # 3. Act: Tentar mudar a senha
    new_pass = "NovaSenhaForte!789"
    response = await client.post("/auth/reset_password", json={
        "token": token,
        "new_password": new_pass
    })

    # 4. Assert Response
    assert response.status_code == 200
    assert "sucesso" in response.json()["message"]

    # 5. Assert Database (Senha mudou?)
    session.expire_all()
    statement = select(User).where(User.email == email_target)
    result = await session.exec(statement)
    updated_user = result.first()

    assert updated_user.senha_hash != get_password_hash(old_pass) # Hash mudou


@pytest.mark.asyncio
async def test_reset_password_wrong_token_type(client, session):
    """
    Testa tentativa de usar um token de ATIVAÇÃO ou REFRESH para resetar senha.
    Deve ser bloqueado (400 Bad Request).
    """
    email_target = "hacker@example.com"
    user = User(
        email=email_target,
        senha_hash=get_password_hash("123"),
        status=Status.Ativo,
        nome="Hacker",
        perfil="Gestor",
        data_nascimento=date(2000, 1, 1)
    )
    session.add(user)
    await session.commit()

    # Gerar token com TIPO ERRADO
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode = {"exp": expire, "sub": email_target, "type": "activation"} # <--- Errado
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    response = await client.post("/auth/reset_password", json={
        "token": token,
        "new_password": "NovaSenha"
    })

    assert response.status_code == 400
    assert "inválido" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_reset_password_invalid_token(client):
    """Testa reset com token totalmente inválido/malformado."""
    response = await client.post("/auth/reset_password", json={
        "token": "token.jwt.falso",
        "new_password": "123"
    })
    
    assert response.status_code == 400