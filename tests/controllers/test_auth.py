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