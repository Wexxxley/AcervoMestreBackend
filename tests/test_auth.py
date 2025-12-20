"""
Testes para autenticação (login, tokens, refresh).
"""
from http import HTTPStatus
import pytest
from freezegun import freeze_time


@pytest.mark.asyncio
async def test_login_success(client, user):
    """Deve retornar token ao fazer login com credenciais válidas."""
    response = await client.post(
        '/auth/login',
        json={'email': user.email, 'password': user.clean_password},
    )
    
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert 'access_token' in data
    assert 'refresh_token' in data


@pytest.mark.asyncio
async def test_login_wrong_email(client, user):
    """Deve retornar 401 com e-mail incorreto."""
    response = await client.post(
        '/auth/login',
        json={'email': 'wrong@test.com', 'password': user.clean_password},
    )
    
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'E-mail ou senha incorretos'}


@pytest.mark.asyncio
async def test_login_wrong_password(client, user):
    """Deve retornar 401 com senha incorreta."""
    response = await client.post(
        '/auth/login',
        json={'email': user.email, 'password': 'wrongpassword'},
    )
    
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'E-mail ou senha incorretos'}


@pytest.mark.asyncio
async def test_login_inactive_user(client, session, user):
    """Deve retornar 403 para usuário inativo."""
    from app.enums.status import Status
    
    # Tornar usuário inativo
    user.status = Status.Inativo
    session.add(user)
    await session.commit()
    
    response = await client.post(
        '/auth/login',
        json={'email': user.email, 'password': user.clean_password},
    )
    
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert 'inativo' in response.json()['detail'].lower()


@pytest.mark.asyncio
async def test_refresh_token_success(client, user):
    """Deve gerar novo access_token com refresh_token válido."""
    # Primeiro login para pegar refresh_token
    response_login = await client.post(
        '/auth/login',
        json={'email': user.email, 'password': user.clean_password},
    )
    refresh_token = response_login.json()['refresh_token']
    
    # Usar refresh_token
    response = await client.post(
        '/auth/refresh_token',
        json={'refresh_token': refresh_token},
    )
    
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert 'access_token' in data
    assert 'refresh_token' in data


@pytest.mark.asyncio
async def test_refresh_token_invalid(client):
    """Deve retornar 401 com refresh_token inválido."""
    response = await client.post(
        '/auth/refresh_token',
        json={'refresh_token': 'invalid_token'},
    )
    
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_token_expired(client, user):
    """Deve retornar 401 ao usar token expirado."""
    with freeze_time('2024-01-01 12:00:00'):
        response = await client.post(
            '/auth/login',
            json={'email': user.email, 'password': user.clean_password},
        )
        token = response.json()['access_token']
    
    # 31 minutos depois (token expira em 30 minutos)
    with freeze_time('2024-01-01 12:31:00'):
        response = await client.get(
            '/users/me',
            headers={'Authorization': f'Bearer {token}'},
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_forgot_password_success(client, user):
    """Deve aceitar solicitação de reset de senha."""
    response = await client.post(
        '/auth/forgot_password',
        json={'email': user.email},
    )
    
    assert response.status_code == HTTPStatus.OK
    assert 'link' in response.json()['message'].lower()


@pytest.mark.asyncio
async def test_forgot_password_nonexistent_email(client):
    """Deve retornar mensagem genérica mesmo com e-mail inexistente (segurança)."""
    response = await client.post(
        '/auth/forgot_password',
        json={'email': 'nonexistent@test.com'},
    )
    
    # Deve retornar 200 para não expor se e-mail existe
    assert response.status_code == HTTPStatus.OK
