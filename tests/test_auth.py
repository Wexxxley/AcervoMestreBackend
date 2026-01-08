from http import HTTPStatus
import pytest
import jwt
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.models.user import User
from app.enums.status import Status
from app.core.config import settings
from app.core.security import (
    get_password_hash,
    create_access_token,
    create_refresh_token,
    create_reset_password_token
)

# ==========================================
# HELPER LOCAL
# ==========================================
def generate_custom_token(sub: str, type: str, expires_delta: timedelta = None):
    """Gera um token JWT manualmente para testes."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    to_encode = {"exp": expire, "sub": str(sub), "type": type}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

# ==========================================
# 1. TESTES DE LOGIN (/auth/login)
# ==========================================

@pytest.mark.asyncio
async def test_login_success(client, user):
    """Deve retornar token ao fazer login com credenciais válidas."""
    password = getattr(user, "clean_password", "123456") 
    
    response = await client.post(
        '/auth/login',
        json={'email': user.email, 'password': password},
    )
    
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert 'access_token' in data
    assert 'refresh_token' in data

@pytest.mark.asyncio
async def test_login_wrong_email(client, user):
    """Deve retornar 401 com e-mail incorreto."""
    password = getattr(user, "clean_password", "123456")
    response = await client.post(
        '/auth/login',
        json={'email': 'wrong@test.com', 'password': password},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED

@pytest.mark.asyncio
async def test_login_wrong_password(client, user):
    """Deve retornar 401 com senha incorreta."""
    response = await client.post(
        '/auth/login',
        json={'email': user.email, 'password': 'wrongpassword'},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED

@pytest.mark.asyncio
async def test_login_inactive_user(client, session):
    """Deve retornar 403 para usuário inativo/pendente."""
    user = User(
        nome="Inativo",
        email="inativo@test.com",
        senha_hash=get_password_hash("123456"),
        perfil="Aluno",
        status=Status.AguardandoAtivacao 
    )
    session.add(user)
    await session.commit()
    
    response = await client.post(
        '/auth/login',
        json={'email': user.email, 'password': '123456'},
    )
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert 'inativo' in response.json()['detail'].lower()

# ==========================================
# 2. TESTES DE REFRESH TOKEN (/auth/refresh_token)
# ==========================================

@pytest.mark.asyncio
async def test_refresh_token_success(client, user):
    """Deve gerar novo access_token com refresh_token válido."""
    refresh_token = create_refresh_token(user.id)
    
    response = await client.post(
        '/auth/refresh_token',
        json={'refresh_token': refresh_token},
    )
    assert response.status_code == HTTPStatus.OK
    assert 'access_token' in response.json()

@pytest.mark.asyncio
async def test_refresh_token_invalid(client):
    """Deve retornar 401 com refresh_token inválido."""
    response = await client.post(
        '/auth/refresh_token',
        json={'refresh_token': 'invalid_token'},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED

@pytest.mark.asyncio
async def test_refresh_token_wrong_type(client, user):
    """Deve falhar se tentar usar um ACCESS token no endpoint de refresh."""
    access_token = create_access_token(user.id) 
    response = await client.post("/auth/refresh_token", json={"refresh_token": access_token})
    assert response.status_code == HTTPStatus.UNAUTHORIZED

@pytest.mark.asyncio
async def test_refresh_token_user_not_found(client, session):
    """Deve falhar se o usuário do token foi deletado do banco."""
    temp_user = User(nome="Temp", email="t@t.com", perfil="Aluno", status=Status.Ativo)
    session.add(temp_user); await session.commit(); await session.refresh(temp_user)
    token = create_refresh_token(temp_user.id)
    
    await session.delete(temp_user); await session.commit()
    
    response = await client.post("/auth/refresh_token", json={"refresh_token": token})
    assert response.status_code == HTTPStatus.UNAUTHORIZED

@pytest.mark.asyncio
async def test_refresh_token_inactive_user(client, session):
    """Deve falhar se o usuário existe mas está INATIVO."""
    u = User(nome="Inativo", email="i@i.com", perfil="Aluno", status=Status.Inativo)
    session.add(u); await session.commit(); await session.refresh(u)
    token = create_refresh_token(u.id)

    response = await client.post("/auth/refresh_token", json={"refresh_token": token})
    
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert "inativo" in response.json()['detail'].lower()

# ==========================================
# 3. TESTES DE ATIVAÇÃO DE CONTA (/auth/activate_account)
# ==========================================

@pytest.mark.asyncio
async def test_activate_account_success(client, session):
    """Deve ativar conta pendente."""
    user = User(nome="Pendente", email="pending@test.com", perfil="Aluno", status=Status.AguardandoAtivacao)
    session.add(user); await session.commit()

    token = generate_custom_token(user.email, "activation")

    response = await client.post("/auth/activate_account", json={
        "token": token, "new_password": "123"
    })
    assert response.status_code == HTTPStatus.OK
    
    await session.refresh(user)
    assert user.status == Status.Ativo

@pytest.mark.asyncio
async def test_activate_account_invalid_token(client):
    """Deve falhar com token inválido."""
    response = await client.post("/auth/activate_account", json={
        "token": "invalid", "new_password": "123"
    })
    assert response.status_code == HTTPStatus.BAD_REQUEST

@pytest.mark.asyncio
async def test_activate_account_wrong_type(client, user):
    """Deve falhar se usar token de acesso."""
    token = create_access_token(user.id) 
    response = await client.post("/auth/activate_account", json={
        "token": token, "new_password": "123"
    })
    assert response.status_code == HTTPStatus.BAD_REQUEST

@pytest.mark.asyncio
async def test_activate_account_user_not_found(client):
    """Deve falhar se e-mail no token não existe."""
    token = generate_custom_token("ghost@test.com", "activation")
    response = await client.post("/auth/activate_account", json={
        "token": token, "new_password": "123"
    })
    assert response.status_code == HTTPStatus.NOT_FOUND

@pytest.mark.asyncio
async def test_activate_account_already_active(client, user):
    """Deve falhar se usuário já estiver ativo."""
    token = generate_custom_token(user.email, "activation")
    response = await client.post("/auth/activate_account", json={
        "token": token, "new_password": "123"
    })
    assert response.status_code == HTTPStatus.BAD_REQUEST

# ==========================================
# 4. TESTES DE ESQUECI MINHA SENHA (/auth/forgot_password)
# ==========================================

@pytest.mark.asyncio
async def test_forgot_password_success(client, user):
    """Deve enviar e-mail se usuário ativo."""
    with patch("app.controllers.authController.send_reset_password_email") as mock_email:
        response = await client.post('/auth/forgot_password', json={'email': user.email})
        assert response.status_code == HTTPStatus.OK
        mock_email.assert_called_once()

@pytest.mark.asyncio
async def test_forgot_password_nonexistent_email(client):
    """Deve retornar 200 e NÃO enviar e-mail se usuário não existe."""
    with patch("app.controllers.authController.send_reset_password_email") as mock_email:
        response = await client.post('/auth/forgot_password', json={'email': 'ghost@test.com'})
        assert response.status_code == HTTPStatus.OK
        mock_email.assert_not_called()

@pytest.mark.asyncio
async def test_forgot_password_inactive_user(client, session):
    """Deve retornar 200 e NÃO enviar e-mail se usuário inativo."""
    u = User(nome="Inativo", email="i2@t.com", perfil="Aluno", status=Status.Inativo)
    session.add(u); await session.commit()

    with patch("app.controllers.authController.send_reset_password_email") as mock_email:
        response = await client.post('/auth/forgot_password', json={'email': u.email})
        assert response.status_code == HTTPStatus.OK
        mock_email.assert_not_called()

# ==========================================
# 5. TESTES DE RESETAR SENHA (/auth/reset_password)
# ==========================================

@pytest.mark.asyncio
async def test_reset_password_success(client, user, session):
    """Deve redefinir a senha."""
    token = create_reset_password_token(user.email)
    response = await client.post("/auth/reset_password", json={
        "token": token, "new_password": "newpass"
    })
    assert response.status_code == HTTPStatus.OK
    
    await session.refresh(user)
    # Testa login com nova senha
    resp_login = await client.post("/auth/login", json={"email": user.email, "password": "newpass"})
    assert resp_login.status_code == HTTPStatus.OK

@pytest.mark.asyncio
async def test_reset_password_invalid_token(client):
    """Deve falhar com token inválido."""
    response = await client.post("/auth/reset_password", json={
        "token": "inv", "new_password": "123"
    })
    assert response.status_code == HTTPStatus.BAD_REQUEST

@pytest.mark.asyncio
async def test_reset_password_wrong_type(client, user):
    """Deve falhar se usar token de acesso."""
    token = create_access_token(user.id)
    response = await client.post("/auth/reset_password", json={
        "token": token, "new_password": "123"
    })
    assert response.status_code == HTTPStatus.BAD_REQUEST

@pytest.mark.asyncio
async def test_reset_password_user_not_found(client):
    """Deve falhar se usuário não existe."""
    token = generate_custom_token("ghost@t.com", "reset_password")
    response = await client.post("/auth/reset_password", json={
        "token": token, "new_password": "123"
    })
    assert response.status_code == HTTPStatus.NOT_FOUND