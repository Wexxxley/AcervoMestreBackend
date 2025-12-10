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
async def test_create_user(client):
    """Testa o fluxo feliz de criação de usuário."""
    response = await client.post("/users/create", json=USER_PAYLOAD)
    
    assert response.status_code == 201
    data = response.json()
    
    # Validações
    assert data["email"] == USER_PAYLOAD["email"]
    assert "id" in data
    assert "senha" not in data  # Garante que UserRead está sendo usado (sem senha)
    assert data["status"] == "Ativo" # Valor default

@pytest.mark.asyncio
async def test_create_user_duplicate_email(client):
    """Testa se a API barra emails duplicados."""
    # 1. Cria o primeiro usuário
    await client.post("/users/create", json=USER_PAYLOAD)
    
    # 2. Tenta criar o segundo exatamente igual
    response = await client.post("/users/create", json=USER_PAYLOAD)
    
    assert response.status_code == 400
    assert "Já existe um usuário cadastrado" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_user_by_id(client):
    """Testa a busca de usuário por ID."""
    # Cria usuário para ter um ID válido
    res_create = await client.post("/users/create", json=USER_PAYLOAD)
    user_id = res_create.json()["id"]

    # Busca pelo ID
    response = await client.get(f"/users/get/{user_id}")
    
    assert response.status_code == 200
    assert response.json()["id"] == user_id
    assert response.json()["nome"] == USER_PAYLOAD["nome"]

@pytest.mark.asyncio
async def test_get_user_not_found(client):
    """Testa erro 404 ao buscar ID inexistente."""
    response = await client.get("/users/get/99999999999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Usuário não encontrado"

@pytest.mark.asyncio
async def test_update_user_patch(client):
    """Testa a atualização parcial de dados."""

    # Cria usuário
    res_create = await client.post("/users/create", json=USER_PAYLOAD)
    user_id = res_create.json()["id"]

    # Atualiza APENAS o nome
    new_data = {"nome": "Nome Atualizado"}
    response = await client.patch(f"/users/patch/{user_id}", json=new_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["nome"] == "Nome Atualizado"
    assert data["email"] == USER_PAYLOAD["email"] # Email não deve mudar

@pytest.mark.asyncio
async def test_delete_user_soft_delete(client, session):
    """
    Testa se o delete faz apenas a exclusão lógica (muda status para Inativo).
    """
    # Cria usuário
    res_create = await client.post("/users/create", json=USER_PAYLOAD)
    user_id = res_create.json()["id"]

    # Deleta via API
    response = await client.delete(f"/users/delete/{user_id}")
    assert response.status_code == 204

    # Verifica no BANCO DE DADOS se o status mudou
    statement = select(User).where(User.id == user_id)
    result = await session.exec(statement)
    db_user = result.first()
    
    assert db_user.status == Status.Inativo

@pytest.mark.asyncio
async def test_get_all_users_pagination(client):
    """Testa a listagem paginada."""
    # Cria 15 usuários fictícios
    for i in range(15):
        payload = USER_PAYLOAD.copy()
        payload["email"] = f"user{i}@test.com"
        await client.post("/users/create", json=payload)

    # Requisita a página 1 com 10 itens
    response = await client.get("/users/get_all?page=1&per_page=10")
    
    assert response.status_code == 200
    data = response.json()
    
    # Valida estrutura de paginação
    assert len(data["items"]) == 10
    assert data["total"] == 15
    assert data["page"] == 1
    assert data["total_pages"] == 2

    # Requisita a página 2 (deve ter os 5 restantes)
    response_p2 = await client.get("/users/get_all?page=2&per_page=10")
    data_p2 = response_p2.json()
    assert len(data_p2["items"]) == 5