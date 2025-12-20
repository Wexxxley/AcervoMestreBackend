"""
Testes para CRUD de usuários.
"""
from http import HTTPStatus
import pytest
from app.enums.perfil import Perfil
from app.enums.status import Status


@pytest.mark.asyncio
async def test_create_user_as_gestor(client, gestor_token):
    """Gestor deve conseguir criar usuário."""
    response = await client.post(
        '/users/create',
        headers={'Authorization': f'Bearer {gestor_token}'},
        json={
            'nome': 'Novo Usuario',
            'email': 'novo@test.com',
            'perfil': 'Professor',
        },
    )
    
    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data['email'] == 'novo@test.com'
    assert data['perfil'] == 'Professor'
    assert data['status'] == 'AguardandoAtivacao'


@pytest.mark.asyncio
async def test_create_user_duplicate_email(client, gestor_token, user):
    """Não deve permitir criar usuário com e-mail duplicado."""
    response = await client.post(
        '/users/create',
        headers={'Authorization': f'Bearer {gestor_token}'},
        json={
            'nome': 'Usuario Duplicado',
            'email': user.email,  # E-mail já existente
            'perfil': 'Professor',
        },
    )
    
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert 'já existe' in response.json()['detail'].lower() or 'já cadastrado' in response.json()['detail'].lower()


@pytest.mark.asyncio
async def test_create_user_without_permission(client, aluno_token):
    """Aluno não deve conseguir criar usuário."""
    response = await client.post(
        '/users/create',
        headers={'Authorization': f'Bearer {aluno_token}'},
        json={
            'nome': 'Tentativa Usuario',
            'email': 'tentativa@test.com',
            'perfil': 'Professor',
        },
    )
    
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_get_user_by_id(client, user, token):
    """Deve retornar usuário por ID."""
    response = await client.get(
        f'/users/get/{user.id}',
        headers={'Authorization': f'Bearer {token}'},
    )
    
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['id'] == user.id
    assert data['email'] == user.email


@pytest.mark.asyncio
async def test_get_user_not_found(client, token):
    """Deve retornar 404 para usuário inexistente."""
    response = await client.get(
        '/users/get/9999',
        headers={'Authorization': f'Bearer {token}'},
    )
    
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_get_all_users(client, user, other_user, token):
    """Deve listar todos os usuários ativos."""
    response = await client.get(
        '/users/get_all?page=1&per_page=10',
        headers={'Authorization': f'Bearer {token}'},
    )
    
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['total'] >= 2
    assert len(data['items']) >= 2


@pytest.mark.asyncio
async def test_get_me(client, user, token):
    """Deve retornar dados do usuário autenticado."""
    response = await client.get(
        '/users/me',
        headers={'Authorization': f'Bearer {token}'},
    )
    
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['id'] == user.id
    assert data['email'] == user.email


@pytest.mark.asyncio
async def test_get_me_without_token(client):
    """Deve retornar 401 sem token."""
    response = await client.get('/users/me')
    
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_update_user_as_gestor(client, user, gestor_token):
    """Gestor deve conseguir atualizar usuário."""
    response = await client.patch(
        f'/users/patch/{user.id}',
        headers={'Authorization': f'Bearer {gestor_token}'},
        json={
            'nome': 'Nome Atualizado',
        },
    )
    
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['nome'] == 'Nome Atualizado'


@pytest.mark.asyncio
async def test_update_user_without_permission(client, user, aluno_token):
    """Aluno não deve conseguir atualizar usuário."""
    response = await client.patch(
        f'/users/patch/{user.id}',
        headers={'Authorization': f'Bearer {aluno_token}'},
        json={
            'nome': 'Tentativa Atualizar',
        },
    )
    
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_delete_user_as_gestor(client, other_user, gestor_token):
    """Gestor deve conseguir deletar usuário."""
    response = await client.delete(
        f'/users/delete/{other_user.id}',
        headers={'Authorization': f'Bearer {gestor_token}'},
    )
    
    assert response.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.asyncio
async def test_delete_user_without_permission(client, other_user, token):
    """Professor não deve conseguir deletar usuário."""
    response = await client.delete(
        f'/users/delete/{other_user.id}',
        headers={'Authorization': f'Bearer {token}'},
    )
    
    assert response.status_code == HTTPStatus.FORBIDDEN
