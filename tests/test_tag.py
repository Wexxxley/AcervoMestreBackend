from http import HTTPStatus
import pytest
from app.models.tag import Tag

# ==========================================
# TESTES DE CRIAÇÃO (POST /tags/create)
# ==========================================

@pytest.mark.asyncio
async def test_criar_tag_sucesso(client, coordenador_token):
    """Deve criar uma nova tag com sucesso."""
    response = await client.post(
        "/tags/create",
        headers={"Authorization": f"Bearer {coordenador_token}"},
        json={"nome": "Nova Tag"}
    )

    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data["nome"] == "Nova Tag"
    assert "id" in data

@pytest.mark.asyncio
async def test_criar_tag_duplicada(client, coordenador_token, session):
    """Não deve permitir criar tags com nomes duplicados."""
    # 1. Cria a primeira tag diretamente no banco ou via API
    tag_existente = Tag(nome="Python")
    session.add(tag_existente)
    await session.commit()

    # 2. Tenta criar a mesma tag via API
    response = await client.post(
        "/tags/create",
        headers={"Authorization": f"Bearer {coordenador_token}"},
        json={"nome": "Python"}
    )

    # 3. Verifica se retornou 400 Bad Request com a mensagem correta
    assert response.status_code == HTTPStatus.BAD_REQUEST
    data = response.json()
    assert "já existe" in data["detail"]

@pytest.mark.asyncio
async def test_criar_tag_sem_auth(client):
    """Não deve criar tag sem token de autenticação."""
    response = await client.post(
        "/tags/create",
        json={"nome": "Tag Sem Auth"}
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED

# ==========================================
# TESTES DE LISTAGEM (GET /tags/get_all)
# ==========================================

@pytest.mark.asyncio
async def test_listar_tags(client, coordenador_token, session):
    """Deve listar todas as tags ordenadas por nome."""
    # Cria algumas tags para garantir que a lista não está vazia
    session.add(Tag(nome="Zebra"))
    session.add(Tag(nome="Alpha"))
    await session.commit()

    response = await client.get(
        "/tags/get_all",
        headers={"Authorization": f"Bearer {coordenador_token}"}
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert len(data) >= 2
    # Verifica ordenação (Alpha deve vir antes de Zebra)
    nomes = [t["nome"] for t in data]
    assert "Alpha" in nomes
    assert "Zebra" in nomes

# ==========================================
# TESTES DE DELEÇÃO (DELETE /tags/delete/{id})
# ==========================================

@pytest.mark.asyncio
async def test_deletar_tag_sucesso(client, coordenador_token, session):
    """Deve deletar uma tag existente."""
    # 1. Cria a tag
    tag = Tag(nome="Tag Para Deletar")
    session.add(tag)
    await session.commit()
    await session.refresh(tag)

    # 2. Deleta via API
    response = await client.delete(
        f"/tags/delete/{tag.id}",
        headers={"Authorization": f"Bearer {coordenador_token}"}
    )

    assert response.status_code == HTTPStatus.NO_CONTENT

    # 3. Verifica se sumiu do banco (opcional, mas recomendado)
    from sqlmodel import select
    stmt = select(Tag).where(Tag.id == tag.id)
    result = await session.exec(stmt)
    assert result.first() is None

@pytest.mark.asyncio
async def test_deletar_tag_inexistente(client, coordenador_token):
    """Deve retornar 404 ao tentar deletar tag que não existe."""
    response = await client.delete(
        "/tags/delete/999999",
        headers={"Authorization": f"Bearer {coordenador_token}"}
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()["detail"] == "Tag não encontrada"