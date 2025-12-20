"""
Testes básicos para validar a infraestrutura
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Testa se a aplicação está respondendo."""
    response = await client.get("/")
    assert response.status_code in [200, 404]  # Aceita ambos pois não temos rota raiz


@pytest.mark.asyncio  
async def test_database_connection(session):
    """Testa se a conexão com o banco funciona."""
    from sqlmodel import select
    from app.models.user import User
    
    # Simples query para validar conexão
    result = await session.execute(select(User))
    users = result.scalars().all()
    assert isinstance(users, list)
