import pytest
import pytest_asyncio 
from sqlmodel import select
from app.models.user import User
from app.enums.status import Status
from app.core.security import get_password_hash

USER_PAYLOAD = {
    "nome": "Wesley Teste",
    "email": "wesley.teste@example.com",
    "senha": "123", 
    "perfil": "Professor", 
    "data_nascimento": "1999-01-01"
}

@pytest_asyncio.fixture 
async def gestor_headers(client, session):
    """
    Cria um usuário Gestor no banco, faz login e retorna os headers com Token.
    """
    gestor_email = "super.gestor@test.com"
    gestor_pass = "senha_super_secreta"
    
    # 1. Cria o Gestor no Banco se não existir
    existing_gestor = await session.exec(select(User).where(User.email == gestor_email))
    if not existing_gestor.first():
        gestor = User(
            nome="Super Gestor",
            email=gestor_email,
            senha_hash=get_password_hash(gestor_pass),
            perfil="Gestor", 
            status=Status.Ativo
        )
        session.add(gestor)
        await session.commit()
    
    # 2. Faz Login para pegar o Token
    response = await client.post("/auth/login", json={
        "email": gestor_email,
        "password": gestor_pass
    })
    
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}


# --- TESTES DE CRIAÇÃO ---
@pytest.mark.asyncio
async def test_create_user_flow_active(client, gestor_headers):
    """Testa o fluxo 1: Criação com senha (status Ativo)."""
    response = await client.post("/users/create", json=USER_PAYLOAD, headers=gestor_headers)
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["email"] == USER_PAYLOAD["email"]
    assert "senha" not in data
    assert data["status"] == Status.Ativo 

@pytest.mark.asyncio
async def test_create_user_flow_invitation(client, gestor_headers):
    """Testa o fluxo 2: Criação sem senha (status AguardandoAtivacao)."""
    payload_invite = USER_PAYLOAD.copy()
    del payload_invite["senha"]
    
    response = await client.post("/users/create", json=payload_invite, headers=gestor_headers)
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["email"] == USER_PAYLOAD["email"]
    assert data["status"] == Status.AguardandoAtivacao 

@pytest.mark.asyncio
async def test_create_user_duplicate_email(client, gestor_headers):
    """Testa se a API barra emails duplicados."""
    await client.post("/users/create", json=USER_PAYLOAD, headers=gestor_headers)
    
    # Tenta criar o segundo exatamente igual
    response = await client.post("/users/create", json=USER_PAYLOAD, headers=gestor_headers)
    
    assert response.status_code == 400
    assert "Já existe um usuário cadastrado" in response.json()["detail"]


# --- TESTES DE LEITURA ---
@pytest.mark.asyncio
async def test_get_user_by_id(client, gestor_headers):
    """Testa a busca de usuário por ID."""
    res_create = await client.post("/users/create", json=USER_PAYLOAD, headers=gestor_headers)
    user_id = res_create.json()["id"]

    response = await client.get(f"/users/get/{user_id}", headers=gestor_headers)
    
    assert response.status_code == 200
    assert response.json()["id"] == user_id

@pytest.mark.asyncio
async def test_get_user_not_found(client, gestor_headers):
    """Testa erro 404 ao buscar ID inexistente."""
    response = await client.get("/users/get/999999", headers=gestor_headers)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_all_users_pagination_and_filter(client, session, gestor_headers):
    """Testa a listagem paginada e o filtro de status."""
    
    # 1. Cria 5 usuários ativos via API
    for i in range(5):
        payload = USER_PAYLOAD.copy()
        payload["email"] = f"active{i}@test.com"
        await client.post("/users/create", json=payload, headers=gestor_headers)

    # 2. Cria 1 usuário Inativo manualmente no banco
    user_inativo = User(
        nome="Inativo 1", 
        email="inativo1@test.com", 
        status=Status.Inativo, 
        perfil="Gestor"
    )
    session.add(user_inativo)
    await session.commit()

    # TESTE A: Busca padrão (somente_ativos=True)
    response = await client.get("/users/get_all?page=1&per_page=10", headers=gestor_headers)
    data = response.json()
    
    assert data["total"] == 6 

    response_all = await client.get("/users/get_all?page=1&per_page=10&somente_ativos=false", headers=gestor_headers)
    data_all = response_all.json()
    
    assert data_all["total"] == 7


# --- TESTES DE ATUALIZAÇÃO E DELETE ---
@pytest.mark.asyncio
async def test_update_user_patch(client, gestor_headers):
    """Testa a atualização parcial de dados."""
    res_create = await client.post("/users/create", json=USER_PAYLOAD, headers=gestor_headers)
    user_id = res_create.json()["id"]

    new_data = {"nome": "Nome Atualizado"}
    response = await client.patch(f"/users/patch/{user_id}", json=new_data, headers=gestor_headers)
    
    assert response.status_code == 200
    assert response.json()["nome"] == "Nome Atualizado"

@pytest.mark.asyncio
async def test_restore_user_success(client, session, gestor_headers):
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
    response = await client.patch(f"/users/restore/{user.id}", headers=gestor_headers)
    
    # 3. Verificar
    assert response.status_code == 200
    assert response.json()["status"] == Status.Ativo

@pytest.mark.asyncio
async def test_restore_user_invalid_status(client, session, gestor_headers):
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

    response = await client.patch(f"/users/restore/{user.id}", headers=gestor_headers)
    assert response.status_code == 400
    assert "nunca foi ativado" in response.json()["detail"]

@pytest.mark.asyncio
async def test_delete_user_soft_delete(client, session, gestor_headers):
    """Testa Soft Delete para usuários Ativos."""
    res_create = await client.post("/users/create", json=USER_PAYLOAD, headers=gestor_headers)
    user_id = res_create.json()["id"]

    # Delete
    response = await client.delete(f"/users/delete/{user_id}", headers=gestor_headers)
    assert response.status_code == 204

    # Verificar no BD
    statement = select(User).where(User.id == user_id)
    result = await session.exec(statement)
    db_user = result.first()
    
    assert db_user is not None
    assert db_user.status == Status.Inativo

@pytest.mark.asyncio
async def test_delete_user_hard_delete(client, session, gestor_headers):
    """Testa Hard Delete para usuários AguardandoAtivacao (Convites)."""
    # 1. Criar convite
    payload = USER_PAYLOAD.copy()
    del payload["senha"]
    res = await client.post("/users/create", json=payload, headers=gestor_headers)
    user_id = res.json()["id"]

    # 2. Deletar
    response = await client.delete(f"/users/delete/{user_id}", headers=gestor_headers)
    assert response.status_code == 204

    # 3. Verificar no BD (Deve ter SUMIDO)
    statement = select(User).where(User.id == user_id)
    result = await session.exec(statement)
    db_user = result.first()
    
    assert db_user is None 

@pytest.mark.asyncio
async def test_resend_invitation_success(client, gestor_headers):
    """Testa reenvio de convite para usuário pendente."""
    # 1. Criar usuário pendente
    payload = USER_PAYLOAD.copy()
    del payload["senha"]
    res = await client.post("/users/create", json=payload, headers=gestor_headers)
    user_id = res.json()["id"]

    # 2. Reenviar
    response = await client.post(f"/users/resend_invitation/{user_id}", headers=gestor_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "E-mail de convite reenviado com sucesso."

@pytest.mark.asyncio
async def test_resend_invitation_fail_active(client, gestor_headers):
    """Testa erro ao tentar reenviar convite para usuário já ativo."""
    # 1. Criar usuário ativo
    res = await client.post("/users/create", json=USER_PAYLOAD, headers=gestor_headers)
    user_id = res.json()["id"]

    # 2. Tentar reenviar
    response = await client.post(f"/users/resend_invitation/{user_id}", headers=gestor_headers)
    
    assert response.status_code == 400
    assert "já está ativo" in response.json()["detail"] or "status" in response.json()["detail"]