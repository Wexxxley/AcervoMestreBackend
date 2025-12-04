import sys
from pathlib import Path

import pytest_asyncio
sys.path.insert(0, str(Path(__file__).parent.parent))

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession 
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from typing import AsyncGenerator

from main import app  # instância do FastAPI 
from app.core.database import get_session 

# CHAMADAS AOS MODELOS
from app.models.user import User 
from app.models.recurso import Recurso

# Configuração do Banco de Dados de Teste (SQLite em Memória)
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def async_engine():
    engine = create_async_engine(DATABASE_URL, echo=False, future=True)
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    
    await engine.dispose()

@pytest_asyncio.fixture
async def session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session_maker = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session

@pytest_asyncio.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Cria um cliente HTTP simulado que usa a sessão de teste."""
    
    async def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    
    app.dependency_overrides.clear()