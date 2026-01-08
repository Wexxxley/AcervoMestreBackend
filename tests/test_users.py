"""
Testes completos para o userController.
"""
from http import HTTPStatus
import pytest
from unittest.mock import AsyncMock, patch
from app.enums.perfil import Perfil
from app.enums.status import Status
from app.models.user import User

# ==========================================
# 1. TESTES DE CRIAÇÃO (CREATE)
# ==========================================

@pytest.mark.asyncio
async def test_create_user_with_password(client, gestor_token):
    """Gestor cria usuário JÁ ATIVO (com senha definida)."""
    # Mesmo que não deva enviar e-mail aqui, mockamos por segurança
    with patch("app.controllers.userController.send_activation_email") as mock_email:
        response = await client.post(
            '/users/create',
            headers={'Authorization': f'Bearer {gestor_token}'},
            json={
                'nome': 'Usuario Ativo',
                'email': 'ativo@test.com',
                'perfil': 'Professor',
                'senha': '123'
            },
        )
        
        assert response.status_code == HTTPStatus.CREATED
        data = response.json()
        assert data['status'] == Status.Ativo
        mock_email.assert_not_called() # Garante que NÃO enviou

@pytest.mark.asyncio
async def test_create_user_without_password(client, gestor_token):
    """Gestor cria usuário PENDENTE (sem senha -> convite)."""
    with patch("app.controllers.userController.send_activation_email") as mock_email:
        response = await client.post(
            '/users/create',
            headers={'Authorization': f'Bearer {gestor_token}'},
            json={
                'nome': 'Usuario Pendente',
                'email': 'pendente@test.com',
                'perfil': 'Professor',
            },
        )
        
        assert response.status_code == HTTPStatus.CREATED
        data = response.json()
        assert data['status'] == Status.AguardandoAtivacao
        mock_email.assert_called_once() # Garante que ENVIOU

@pytest.mark.asyncio
async def test_create_user_duplicate_email(client, gestor_token, user):
    """Erro ao criar e-mail duplicado."""
    # CORREÇÃO AQUI: Mockamos o email mesmo esperando erro no final
    with patch("app.controllers.userController.send_activation_email") as mock_email:
        response = await client.post(
            '/users/create',
            headers={'Authorization': f'Bearer {gestor_token}'},
            json={
                'nome': 'Duplicado',
                'email': user.email, # Já existe
                'perfil': 'Professor',
                # Sem senha, cairia no fluxo de envio de email
            },
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        # O sistema pode ou não ter chamado o add_task antes do erro, 
        # mas o importante é que o mock impediu o envio real.

@pytest.mark.asyncio
async def test_create_user_forbidden(client, aluno_token):
    """Aluno não cria usuário."""
    response = await client.post(
        '/users/create',
        headers={'Authorization': f'Bearer {aluno_token}'},
        json={'nome': 'Teste', 'email': 't@t.com', 'perfil': 'Aluno'}
    )
    assert response.status_code == HTTPStatus.FORBIDDEN

# ==========================================
# 2. TESTES DE LEITURA (GET)
# ==========================================

@pytest.mark.asyncio
async def test_get_user_by_id(client, user, token):
    """Retorna usuário por ID."""
    response = await client.get(
        f'/users/get/{user.id}',
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()['id'] == user.id

@pytest.mark.asyncio
async def test_get_user_not_found(client, token):
    """Retorna 404."""
    response = await client.get('/users/get/99999', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == HTTPStatus.NOT_FOUND

@pytest.mark.asyncio
async def test_get_all_users(client, token):
    """Lista usuários."""
    response = await client.get('/users/get_all', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == HTTPStatus.OK
    assert response.json()['total'] >= 1

@pytest.mark.asyncio
async def test_get_me(client, token, user):
    """Dados do usuário logado."""
    response = await client.get('/users/me', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == HTTPStatus.OK
    assert response.json()['email'] == user.email

# ==========================================
# 3. TESTES DE REENVIO DE CONVITE (RESEND)
# ==========================================

@pytest.mark.asyncio
async def test_resend_invitation_success(client, gestor_token, session):
    """Reenvia convite para usuário AguardandoAtivacao."""
    u = User(nome="Pendente", email="p@t.com", perfil="Aluno", status=Status.AguardandoAtivacao)
    session.add(u)
    await session.commit()
    
    with patch("app.controllers.userController.send_activation_email") as mock_email:
        response = await client.post(
            f'/users/resend_invitation/{u.id}',
            headers={'Authorization': f'Bearer {gestor_token}'}
        )
        assert response.status_code == HTTPStatus.OK
        mock_email.assert_called_once()

@pytest.mark.asyncio
async def test_resend_invitation_wrong_status(client, gestor_token, user):
    """Erro se usuário já estiver ativo."""
    # Mesmo esperando erro, mockamos por segurança
    with patch("app.controllers.userController.send_activation_email") as mock_email:
        response = await client.post(
            f'/users/resend_invitation/{user.id}',
            headers={'Authorization': f'Bearer {gestor_token}'}
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        mock_email.assert_not_called()

@pytest.mark.asyncio
async def test_resend_invitation_not_found(client, gestor_token):
    """Erro se usuário não existe."""
    response = await client.post(
        '/users/resend_invitation/99999',
        headers={'Authorization': f'Bearer {gestor_token}'}
    )
    assert response.status_code == HTTPStatus.NOT_FOUND

# ==========================================
# 4. TESTES DE UPDATE (PATCH)
# ==========================================

@pytest.mark.asyncio
async def test_update_user(client, gestor_token, user):
    """Atualiza usuário."""
    response = await client.patch(
        f'/users/patch/{user.id}',
        headers={'Authorization': f'Bearer {gestor_token}'},
        json={'nome': 'Editado'}
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()['nome'] == 'Editado'

@pytest.mark.asyncio
async def test_update_user_not_found(client, gestor_token):
    """Atualiza usuário inexistente."""
    response = await client.patch(
        '/users/patch/99999',
        headers={'Authorization': f'Bearer {gestor_token}'},
        json={'nome': 'X'}
    )
    assert response.status_code == HTTPStatus.NOT_FOUND

# ==========================================
# 5. TESTES DE RESTAURAR (RESTORE)
# ==========================================

@pytest.mark.asyncio
async def test_restore_user_success(client, gestor_token, session):
    """Restaura usuário Inativo -> Ativo."""
    u = User(nome="Inativo", email="i@t.com", perfil="Aluno", status=Status.Inativo)
    session.add(u)
    await session.commit()
    
    response = await client.patch(
        f'/users/restore/{u.id}',
        headers={'Authorization': f'Bearer {gestor_token}'}
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()['status'] == Status.Ativo

@pytest.mark.asyncio
async def test_restore_user_invalid_status(client, gestor_token, user):
    """Erro ao restaurar usuário que já está ativo."""
    response = await client.patch(
        f'/users/restore/{user.id}',
        headers={'Authorization': f'Bearer {gestor_token}'}
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST

# ==========================================
# 6. TESTES DE DELEÇÃO (DELETE)
# ==========================================

@pytest.mark.asyncio
async def test_soft_delete_active_user(client, gestor_token, user, session):
    """Soft Delete: Usuário ativo vira inativo."""
    response = await client.delete(
        f'/users/delete/{user.id}',
        headers={'Authorization': f'Bearer {gestor_token}'}
    )
    assert response.status_code == HTTPStatus.NO_CONTENT
    
    await session.refresh(user)
    assert user.status == Status.Inativo

@pytest.mark.asyncio
async def test_hard_delete_pending_user(client, gestor_token, session):
    """Hard Delete: Usuário pendente é removido do banco."""
    u = User(nome="Pendente", email="pend@t.com", perfil="Aluno", status=Status.AguardandoAtivacao)
    session.add(u)
    await session.commit()
    uid = u.id
    
    response = await client.delete(
        f'/users/delete/{uid}',
        headers={'Authorization': f'Bearer {gestor_token}'}
    )
    assert response.status_code == HTTPStatus.NO_CONTENT
    
    deleted_user = await session.get(User, uid)
    assert deleted_user is None

# ==========================================
# 7. TESTES DE IMAGEM DE PERFIL (MOCK S3)
# ==========================================
@pytest.mark.asyncio
async def test_update_profile_image_success(client, token, user):
    """Usuário atualiza a própria foto (Upload)."""
    
    # Mockamos a instância s3_service importada DENTRO do controller
    with patch("app.controllers.userController.s3_service") as mock_s3:
        
        # 1. Configurar upload_file (Comportamento Async)
        async def fake_upload(file):
            return {
                "storage_key": "new-image.png",
                "mime_type": "image/png",
                "tamanho_bytes": 1024
            }
        mock_s3.upload_file.side_effect = fake_upload
        
        # 2. Configurar delete_file (Comportamento Async para evitar erro de await)
        # Isso resolve o aviso "MagicMock can't be used in await"
        mock_s3.delete_file = AsyncMock()
        
        # 3. Configurar get_file_url (Comportamento Síncrono)
        # Forçamos retornar string. Se o controller chamar sem await, recebe string.
        mock_s3.get_file_url.return_value = "http://fake-url.com/img.png"
        
        response = await client.patch(
            f'/users/{user.id}/image',
            headers={'Authorization': f'Bearer {token}'},
            files={'file': ('teste.png', b'conteudo', 'image/png')}
        )
        
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data['url_perfil'] == "http://fake-url.com/img.png"
        
        # Verifica chamadas
        mock_s3.upload_file.assert_called_once()
        # Nota: delete_file pode não ser chamado se o usuário não tinha foto antes.
        # Se o user fixture tiver foto, assert_called_once() funcionaria.

@pytest.mark.asyncio
async def test_remove_profile_image_success(client, token, user, session):
    """Usuário remove a foto (sem enviar arquivo)."""
    # Prepara usuário com foto
    user.path_img = "old-image.png"
    session.add(user)
    await session.commit()
    
    with patch("app.controllers.userController.s3_service") as mock_s3:
        # Configurar delete_file como AsyncMock para aceitar o 'await' do controller
        mock_s3.delete_file = AsyncMock()
        
        response = await client.patch(
            f'/users/{user.id}/image',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data['url_perfil'] is None
        
        # Verifica se tentou deletar a imagem antiga
        mock_s3.delete_file.assert_called_once_with("old-image.png")