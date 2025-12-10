import pytest
from sqlmodel import select
from app.models.user import User
from app.enums.status import Status

# --- DADOS MOCK PARA TESTES ---
USER_PAYLOAD = {
    "nome": "Wesley Teste",
    "email": "wesley.teste@example.com",
    "senha": "123", 
    "perfil": "Gestor", 
    "data_nascimento": "1999-01-01"
}

@pytest.mark.asyncio
async def test_create_user_flow_active(client):
    """Testa o fluxo 1: Criação com senha (status Ativo)."""
    response = await client.post("/users/create", json=USER_PAYLOAD)
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["email"] == USER_PAYLOAD["email"]
    assert "senha" not in data
    assert data["status"] == Status.Ativo 

@pytest.mark.asyncio
async def test_create_user_flow_invitation(client):
    """Testa o fluxo 2: Criação sem senha (status AguardandoAtivacao)."""
    # Remove a senha do payload
    payload_invite = USER_PAYLOAD.copy()
    del payload_invite["senha"]
    
    response = await client.post("/users/create", json=payload_invite)
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["email"] == USER_PAYLOAD["email"]
    assert data["status"] == Status.AguardandoAtivacao 

@pytest.mark.asyncio
async def test_create_user_duplicate_email(client):
    """Testa se a API barra emails duplicados."""
    await client.post("/users/create", json=USER_PAYLOAD)
    
    # Tenta criar o segundo exatamente igual
    response = await client.post("/users/create", json=USER_PAYLOAD)
    
    assert response.status_code == 400
    assert "Já existe um usuário cadastrado" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_user_by_id(client):
    """Testa a busca de usuário por ID."""
    res_create = await client.post("/users/create", json=USER_PAYLOAD)
    user_id = res_create.json()["id"]

    response = await client.get(f"/users/get/{user_id}")
    
    assert response.status_code == 200
    assert response.json()["id"] == user_id

@pytest.mark.asyncio
async def test_get_user_not_found(client):
    """Testa erro 404 ao buscar ID inexistente."""
    response = await client.get("/users/get/999999")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_all_users_pagination_and_filter(client, session):
    """Testa a listagem paginada e o filtro de status."""
    
    # 1. Cria 5 usuários ativos via API
    for i in range(5):
        payload = USER_PAYLOAD.copy()
        payload["email"] = f"active{i}@test.com"
        await client.post("/users/create", json=payload)

    # 2. Cria 2 usuários Inativos manualmente no banco
    user_inativo = User(
        nome="Inativo 1", 
        email="inativo1@test.com", 
        status=Status.Inativo, 
        perfil="Gestor"
    )
    session.add(user_inativo)
    await session.commit()

    # TESTE A: Busca padrão (somente_ativos=True)
    response = await client.get("/users/get_all?page=1&per_page=10")
    data = response.json()
    assert data["total"] == 5 # Só deve contar os ativos

    # TESTE B: Busca sem filtro (somente_ativos=False)
    response_all = await client.get("/users/get_all?page=1&per_page=10&somente_ativos=false")
    data_all = response_all.json()
    assert data_all["total"] == 6 # 5 ativos + 1 inativo


@pytest.mark.asyncio
async def test_update_user_patch(client):
    """Testa a atualização parcial de dados."""
    res_create = await client.post("/users/create", json=USER_PAYLOAD)
    user_id = res_create.json()["id"]

    new_data = {"nome": "Nome Atualizado"}
    response = await client.patch(f"/users/patch/{user_id}", json=new_data)
    
    assert response.status_code == 200
    assert response.json()["nome"] == "Nome Atualizado"

@pytest.mark.asyncio
async def test_restore_user_success(client, session):
    """Testa a restauração de um usuário Inativo para Ativo."""
    # 1. Preparar: Usuário Inativo
    user = User(
        nome="Deletado", 
        email="del@test.com", 
        status=Status.Inativo, 
        perfil="Gestor",
        senha_hash="hash"
    )
    session.add(user)
    await session.commit()
    
    # 2. Agir: Restaurar
    response = await client.patch(f"/users/restore/{user.id}")
    
    # 3. Verificar
    assert response.status_code == 200
    assert response.json()["status"] == Status.Ativo

@pytest.mark.asyncio
async def test_restore_user_invalid_status(client, session):
    """Testa erro ao tentar restaurar alguém que não está Inativo."""
    # Usuário AguardandoAtivacao
    user = User(
        nome="Novo", 
        email="novo@test.com", 
        status=Status.AguardandoAtivacao, 
        perfil="Gestor"
    )
    session.add(user)
    await session.commit()

    response = await client.patch(f"/users/restore/{user.id}")
    assert response.status_code == 400
    assert "nunca foi ativado" in response.json()["detail"]

@pytest.mark.asyncio
async def test_delete_user_soft_delete(client, session):
    """Testa Soft Delete para usuários Ativos."""
    res_create = await client.post("/users/create", json=USER_PAYLOAD)
    user_id = res_create.json()["id"]

    # Delete
    response = await client.delete(f"/users/delete/{user_id}")
    assert response.status_code == 204

    # Verificar no BD
    statement = select(User).where(User.id == user_id)
    result = await session.exec(statement)
    db_user = result.first()
    
    assert db_user is not None
    assert db_user.status == Status.Inativo

@pytest.mark.asyncio
async def test_delete_user_hard_delete(client, session):
    """Testa Hard Delete para usuários AguardandoAtivacao (Convites)."""
    # 1. Criar convite
    payload = USER_PAYLOAD.copy()
    del payload["senha"]
    res = await client.post("/users/create", json=payload)
    user_id = res.json()["id"]

    # 2. Deletar
    response = await client.delete(f"/users/delete/{user_id}")
    assert response.status_code == 204

    # 3. Verificar no BD (Deve ter SUMIDO)
    statement = select(User).where(User.id == user_id)
    result = await session.exec(statement)
    db_user = result.first()
    
    assert db_user is None # Hard delete confirmado

@pytest.mark.asyncio
async def test_resend_invitation_success(client, session):
    """Testa reenvio de convite para usuário pendente."""
    # 1. Criar usuário pendente
    payload = USER_PAYLOAD.copy()
    del payload["senha"]
    res = await client.post("/users/create", json=payload)
    user_id = res.json()["id"]

    # 2. Reenviar
    response = await client.post(f"/users/resend_invitation/{user_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "E-mail de convite reenviado com sucesso."

@pytest.mark.asyncio
async def test_resend_invitation_fail_active(client):
    """Testa erro ao tentar reenviar convite para usuário já ativo."""
    # 1. Criar usuário ativo
    res = await client.post("/users/create", json=USER_PAYLOAD)
    user_id = res.json()["id"]

    # 2. Tentar reenviar
    response = await client.post(f"/users/resend_invitation/{user_id}")
    
    assert response.status_code == 400
    assert "já está ativo" in response.json()["detail"] or "status" in response.json()["detail"]