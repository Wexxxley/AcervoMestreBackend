import sys
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime

import pytest
import pytest_asyncio
import factory
import factory.fuzzy

sys.path.insert(0, str(Path(__file__).parent.parent))

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import event
from sqlmodel import SQLModel, select
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator
from unittest.mock import AsyncMock
from testcontainers.postgres import PostgresContainer

from main import app
from app.core.database import get_session
from app.models.user import User
from app.models.recurso import Recurso
from app.models.playlist import Playlist
from app.enums.perfil import Perfil
from app.enums.status import Status
from app.enums.visibilidade import Visibilidade
from app.enums.estrutura_recurso import EstruturaRecurso
from app.core.security import get_password_hash


# ============================================================================
# Fixtures de Engine e Session
# ============================================================================

@pytest_asyncio.fixture(scope='session')
async def engine():
    """Engine com PostgreSQL usando TestContainers."""
    postgres = PostgresContainer('postgres:16', driver='psycopg')
    postgres.start()
    
    try:
        # Criar URL de conexão assíncrona
        connection_url = postgres.get_connection_url().replace(
            'postgresql+psycopg://', 'postgresql+asyncpg://'
        )
        
        _engine = create_async_engine(
            connection_url,
            echo=False,
            poolclass=NullPool,  # Evita problemas com pool de conexões
        )
        
        # Criar tabelas
        async with _engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        
        yield _engine
        
        # Cleanup
        await _engine.dispose()
        
    finally:
        postgres.stop()


@pytest_asyncio.fixture
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Sessão assíncrona com rollback após cada teste."""
    connection = await engine.connect()
    transaction = await connection.begin()
    
    session = AsyncSession(bind=connection, expire_on_commit=False)
    
    yield session
    
    await session.close()
    await transaction.rollback()
    await connection.close()


# ============================================================================
# Fixture de Cliente HTTP
# ============================================================================

@pytest_asyncio.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Cliente HTTP assíncrono que usa a sessão de teste."""
    
    async def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override

    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test"
    ) as c:
        yield c
    
    app.dependency_overrides.clear()


# ============================================================================
# Mock de Tempo para Timestamps
# ============================================================================

@asynccontextmanager
async def _mock_db_time(*, model, time=datetime(2024, 1, 1)):
    """Mock de timestamps created_at e updated_at."""
    def fake_time_hook(mapper, connection, target):
        if hasattr(target, 'criado_em'):
            target.criado_em = time
        if hasattr(target, 'atualizado_em'):
            target.atualizado_em = time

    event.listen(model, 'before_insert', fake_time_hook)
    yield time
    event.remove(model, 'before_insert', fake_time_hook)


@pytest.fixture
def mock_db_time():
    """Fixture que retorna função para mockar timestamps."""
    return _mock_db_time


# ============================================================================
# Mock de Serviços Externos
# ============================================================================

@pytest_asyncio.fixture(autouse=True)
async def mock_email_service(monkeypatch):
    """Bloqueia envio de e-mails em testes."""
    from app.core import mail
    
    async def mock_send(*args, **kwargs):
        return None
    
    mock = AsyncMock(side_effect=mock_send)
    monkeypatch.setattr(mail, "send_activation_email", mock)
    monkeypatch.setattr(mail, "send_reset_password_email", mock)
    return mock


@pytest_asyncio.fixture(autouse=True)
async def mock_s3_service(monkeypatch):
    """Bloqueia operações S3/MinIO em testes."""
    mock_upload = AsyncMock(return_value={
        "storage_key": "test-key-123.pdf",
        "mime_type": "application/pdf",
        "tamanho_bytes": 1024
    })
    mock_delete = AsyncMock(return_value=True)
    mock_get_url = AsyncMock(return_value="http://test.com/file.pdf")
    
    monkeypatch.setattr("app.services.s3_service.s3_service.upload_file", mock_upload)
    monkeypatch.setattr("app.services.s3_service.s3_service.delete_file", mock_delete)
    monkeypatch.setattr("app.services.s3_service.s3_service.get_file_url", mock_get_url)
    
    return {
        "upload": mock_upload,
        "delete": mock_delete,
        "get_url": mock_get_url
    }


# ============================================================================
# Factories para Modelos
# ============================================================================

class UserFactory(factory.Factory):
    """Factory para criar usuários de teste."""
    class Meta:
        model = User

    nome = factory.Sequence(lambda n: f'User Test {n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.nome.lower().replace(" ", "")}@test.com')
    perfil = Perfil.Professor
    status = Status.Ativo
    senha_hash = factory.LazyFunction(lambda: get_password_hash('senha123'))


class RecursoFactory(factory.Factory):
    """Factory para criar recursos de teste."""
    class Meta:
        model = Recurso

    titulo = factory.Sequence(lambda n: f'Recurso Teste {n}')
    descricao = factory.Faker('text', max_nb_chars=200)
    visibilidade = Visibilidade.PUBLICO
    estrutura = EstruturaRecurso.NOTA
    conteudo_markdown = factory.Faker('text', max_nb_chars=500)
    autor_id = 1
    is_destaque = False
    visualizacoes = 0
    downloads = 0
    curtidas = 0


class PlaylistFactory(factory.Factory):
    """Factory para criar playlists de teste."""
    class Meta:
        model = Playlist

    titulo = factory.Sequence(lambda n: f'Playlist Teste {n}')
    descricao = factory.Faker('text', max_nb_chars=200)
    autor_id = 1


# ============================================================================
# Fixtures de Usuários
# ============================================================================

@pytest_asyncio.fixture
async def user(session: AsyncSession):
    """Usuário de teste padrão (Professor)."""
    pwd = 'senha123'
    user = UserFactory(senha_hash=get_password_hash(pwd))
    
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    # Adicionar como atributo Python (não field do modelo)
    object.__setattr__(user, 'clean_password', pwd)
    return user


@pytest_asyncio.fixture
async def aluno_user(session: AsyncSession):
    """Usuário de teste com perfil Aluno."""
    pwd = 'senha123'
    user = UserFactory(
        nome="Aluno Teste",
        email="aluno@test.com",
        perfil=Perfil.Aluno,
        senha_hash=get_password_hash(pwd)
    )
    
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    object.__setattr__(user, 'clean_password', pwd)
    return user


@pytest_asyncio.fixture
async def coordenador_user(session: AsyncSession):
    """Usuário de teste com perfil Coordenador."""
    pwd = 'senha123'
    user = UserFactory(
        nome="Coordenador Teste",
        email="coordenador@test.com",
        perfil=Perfil.Coordenador,
        senha_hash=get_password_hash(pwd)
    )
    
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    object.__setattr__(user, 'clean_password', pwd)
    return user


@pytest_asyncio.fixture
async def gestor_user(session: AsyncSession):
    """Usuário de teste com perfil Gestor."""
    pwd = 'senha123'
    user = UserFactory(
        nome="Gestor Teste",
        email="gestor@test.com",
        perfil=Perfil.Gestor,
        senha_hash=get_password_hash(pwd)
    )
    
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    object.__setattr__(user, 'clean_password', pwd)
    return user


@pytest_asyncio.fixture
async def other_user(session: AsyncSession):
    """Outro usuário de teste (para testar permissões)."""
    user = UserFactory(nome="Other User", email="other@test.com")
    
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    return user


# ============================================================================
# Fixtures de Tokens
# ============================================================================

@pytest_asyncio.fixture
async def token(client: AsyncClient, user: User):
    """Token de acesso para usuário padrão."""
    response = await client.post(
        '/auth/login',
        json={'email': user.email, 'password': user.clean_password},
    )
    return response.json()['access_token']


@pytest_asyncio.fixture
async def aluno_token(client: AsyncClient, aluno_user: User):
    """Token de acesso para usuário Aluno."""
    response = await client.post(
        '/auth/login',
        json={'email': aluno_user.email, 'password': aluno_user.clean_password},
    )
    return response.json()['access_token']


@pytest_asyncio.fixture
async def coordenador_token(client: AsyncClient, coordenador_user: User):
    """Token de acesso para usuário Coordenador."""
    response = await client.post(
        '/auth/login',
        json={'email': coordenador_user.email, 'password': coordenador_user.clean_password},
    )
    return response.json()['access_token']


@pytest_asyncio.fixture
async def gestor_token(client: AsyncClient, gestor_user: User):
    """Token de acesso para usuário Gestor."""
    response = await client.post(
        '/auth/login',
        json={'email': gestor_user.email, 'password': gestor_user.clean_password},
    )
    return response.json()['access_token']


# ============================================================================
# Fixtures de Recursos e Playlists
# ============================================================================

@pytest_asyncio.fixture
async def recurso(session: AsyncSession, user: User):
    """Recurso público de teste (tipo NOTA)."""
    recurso = RecursoFactory(autor_id=user.id)
    
    session.add(recurso)
    await session.commit()
    await session.refresh(recurso)
    
    return recurso


@pytest_asyncio.fixture
async def recurso_privado(session: AsyncSession, user: User):
    """Recurso privado de teste."""
    recurso = RecursoFactory(
        autor_id=user.id,
        visibilidade=Visibilidade.PRIVADO
    )
    
    session.add(recurso)
    await session.commit()
    await session.refresh(recurso)
    
    return recurso


@pytest_asyncio.fixture
async def playlist(session: AsyncSession, user: User):
    """Playlist de teste."""
    playlist = PlaylistFactory(autor_id=user.id)
    
    session.add(playlist)
    await session.commit()
    await session.refresh(playlist)
    
    return playlist


@pytest_asyncio.fixture
async def recursos_multiplos(session: AsyncSession, user: User):
    """Fixture que retorna 3 recursos de teste."""
    recursos = []
    for i in range(3):
        recurso = RecursoFactory(
            titulo=f'Recurso {i+1}',
            autor_id=user.id
        )
        session.add(recurso)
        recursos.append(recurso)
    
    await session.commit()
    
    for r in recursos:
        await session.refresh(r)
    
    return recursos
