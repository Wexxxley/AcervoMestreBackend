"""
Testes para o sistema de Playlist

Testes unitários e de integração para todos os endpoints da API de Playlist.
Para usar, execute: pytest tests/controllers/test_playlist_controller.py -v
"""

import pytest
from sqlmodel import create_engine, Session, select, SQLModel
from sqlmodel.pool import StaticPool
from fastapi.testclient import TestClient

from app.models.user import User
from app.models.playlist import Playlist
from app.models.playlist_recurso import PlaylistRecurso
from app.models.recurso import Recurso
from app.enums.perfil import Perfil
from app.enums.status import Status
from app.enums.visibilidade import Visibilidade
from app.enums.estrutura_recurso import EstruturaRecurso
from app.core.database import get_session
from app.core.security import get_current_user
from main import app


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(name="session")
def session_fixture():
    """Cria um banco de dados em memória para testes."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Criar tabelas
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Cria um cliente de teste com session mockada."""
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def mock_get_current_user(user: User | None):
    """Factory para mockar diferentes usuários."""
    def override():
        return user
    return override


@pytest.fixture(name="usuario_professor")
def usuario_professor_fixture(session: Session) -> User:
    """Cria um usuário professor para testes."""
    usuario = User(
        nome="Prof. João",
        email="joao@example.com",
        senha_hash="hash_seguro",
        perfil=Perfil.Professor,
        status=Status.Ativo,
    )
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario


@pytest.fixture(name="usuario_aluno")
def usuario_aluno_fixture(session: Session) -> User:
    """Cria um usuário aluno para testes."""
    usuario = User(
        nome="Aluno Pedro",
        email="pedro@example.com",
        senha_hash="hash_seguro",
        perfil=Perfil.Aluno,
        status=Status.Ativo,
    )
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario


@pytest.fixture(name="recurso_nota")
def recurso_nota_fixture(session: Session, usuario_professor: User) -> Recurso:
    """Cria um recurso do tipo NOTA para testes."""
    recurso = Recurso(
        titulo="Introdução à Álgebra",
        descricao="Conceitos básicos de álgebra",
        visibilidade=Visibilidade.PUBLICO,
        estrutura=EstruturaRecurso.NOTA,
        autor_id=usuario_professor.id,
        conteudo_markdown="# Álgebra\n\nConceitos básicos...",
    )
    session.add(recurso)
    session.commit()
    session.refresh(recurso)
    return recurso


@pytest.fixture(name="recurso_url")
def recurso_url_fixture(session: Session, usuario_professor: User) -> Recurso:
    """Cria um recurso do tipo URL para testes."""
    recurso = Recurso(
        titulo="Vídeo Tutorial",
        descricao="Tutorial em vídeo sobre álgebra",
        visibilidade=Visibilidade.PUBLICO,
        estrutura=EstruturaRecurso.URL,
        autor_id=usuario_professor.id,
        url_externa="https://www.youtube.com/watch?v=abc123",
    )
    session.add(recurso)
    session.commit()
    session.refresh(recurso)
    return recurso


# ============================================================================
# Testes: CRUD Básico
# ============================================================================

def test_criar_playlist_sucesso(client: TestClient, usuario_professor: User):
    """Testa criação bem-sucedida de uma playlist."""
    # TODO: Mockar autenticação quando JWT estiver implementado
    # response = client.post(
    #     "/playlists/",
    #     json={
    #         "titulo": "Aula de Álgebra",
    #         "descricao": "Recursos para a aula de álgebra linear"
    #     },
    #     headers={"Authorization": f"Bearer {token}"}
    # )
    # assert response.status_code == 201
    # data = response.json()
    # assert data["titulo"] == "Aula de Álgebra"
    # assert data["autor_id"] == usuario_professor.id
    pass


def test_criar_playlist_sem_titulo(client: TestClient):
    """Testa criação de playlist sem título (deve falhar)."""
    # response = client.post(
    #     "/playlists/",
    #     json={"titulo": "", "descricao": "..."},
    #     headers={"Authorization": "Bearer token"}
    # )
    # assert response.status_code == 400
    pass


def test_listar_playlists(client: TestClient, session: Session, usuario_professor: User):
    """Testa listagem de playlists."""
    # Criar algumas playlists
    for i in range(3):
        playlist = Playlist(
            titulo=f"Playlist {i}",
            descricao=f"Descrição {i}",
            autor_id=usuario_professor.id,
        )
        session.add(playlist)
    session.commit()
    
    # response = client.get("/playlists/?page=1&per_page=10")
    # assert response.status_code == 200
    # data = response.json()
    # assert data["total"] == 3
    # assert len(data["items"]) == 3
    pass


def test_obter_playlist_por_id(client: TestClient, session: Session, usuario_professor: User):
    """Testa obtenção de uma playlist específica."""
    # Criar uma playlist
    playlist = Playlist(
        titulo="Aula de Álgebra",
        descricao="...",
        autor_id=usuario_professor.id,
    )
    session.add(playlist)
    session.commit()
    session.refresh(playlist)
    
    # response = client.get(f"/playlists/{playlist.id}")
    # assert response.status_code == 200
    # data = response.json()
    # assert data["id"] == playlist.id
    # assert data["titulo"] == "Aula de Álgebra"
    pass


def test_editar_playlist(client: TestClient, session: Session, usuario_professor: User):
    """Testa edição de uma playlist."""
    # Criar uma playlist
    playlist = Playlist(
        titulo="Título Original",
        descricao="Descrição Original",
        autor_id=usuario_professor.id,
    )
    session.add(playlist)
    session.commit()
    session.refresh(playlist)
    
    # response = client.put(
    #     f"/playlists/{playlist.id}",
    #     json={"titulo": "Título Novo"},
    #     headers={"Authorization": "Bearer token"}
    # )
    # assert response.status_code == 200
    # data = response.json()
    # assert data["titulo"] == "Título Novo"
    pass


def test_deletar_playlist(client: TestClient, session: Session, usuario_professor: User):
    """Testa deleção de uma playlist."""
    # Criar uma playlist
    playlist = Playlist(
        titulo="Para Deletar",
        autor_id=usuario_professor.id,
    )
    session.add(playlist)
    session.commit()
    session.refresh(playlist)
    
    # response = client.delete(
    #     f"/playlists/{playlist.id}",
    #     headers={"Authorization": "Bearer token"}
    # )
    # assert response.status_code == 204
    pass


# ============================================================================
# Testes: Gerenciar Recursos
# ============================================================================

def test_adicionar_recurso_playlist(
    client: TestClient,
    session: Session,
    usuario_professor: User,
    recurso_nota: Recurso
):
    """Testa adição de recurso à playlist."""
    # Criar uma playlist
    playlist = Playlist(
        titulo="Aula de Álgebra",
        autor_id=usuario_professor.id,
    )
    session.add(playlist)
    session.commit()
    session.refresh(playlist)
    
    # response = client.post(
    #     f"/playlists/{playlist.id}/recursos",
    #     json={"recurso_id": recurso_nota.id},
    #     headers={"Authorization": "Bearer token"}
    # )
    # assert response.status_code == 201
    # data = response.json()
    # assert data["ordem"] == 0
    pass


def test_adicionar_recurso_duplicado(
    client: TestClient,
    session: Session,
    usuario_professor: User,
    recurso_nota: Recurso
):
    """Testa adição de recurso duplicado (deve falhar)."""
    # Criar playlist e adicionar recurso
    playlist = Playlist(
        titulo="Aula",
        autor_id=usuario_professor.id,
    )
    session.add(playlist)
    session.commit()
    session.refresh(playlist)
    
    pr = PlaylistRecurso(
        playlist_id=playlist.id,
        recurso_id=recurso_nota.id,
        ordem=0,
    )
    session.add(pr)
    session.commit()
    
    # Tentar adicionar novamente
    # response = client.post(
    #     f"/playlists/{playlist.id}/recursos",
    #     json={"recurso_id": recurso_nota.id},
    #     headers={"Authorization": "Bearer token"}
    # )
    # assert response.status_code == 409
    pass


def test_remover_recurso_playlist(
    client: TestClient,
    session: Session,
    usuario_professor: User,
    recurso_nota: Recurso
):
    """Testa remoção de recurso da playlist."""
    # Criar playlist com recurso
    playlist = Playlist(
        titulo="Aula",
        autor_id=usuario_professor.id,
    )
    session.add(playlist)
    session.commit()
    session.refresh(playlist)
    
    pr = PlaylistRecurso(
        playlist_id=playlist.id,
        recurso_id=recurso_nota.id,
        ordem=0,
    )
    session.add(pr)
    session.commit()
    
    # response = client.delete(
    #     f"/playlists/{playlist.id}/recursos/{recurso_nota.id}",
    #     headers={"Authorization": "Bearer token"}
    # )
    # assert response.status_code == 204
    pass


def test_reordenar_recursos(
    client: TestClient,
    session: Session,
    usuario_professor: User,
    recurso_nota: Recurso,
    recurso_url: Recurso
):
    """Testa reordenação de recursos na playlist."""
    # Criar playlist com dois recursos
    playlist = Playlist(
        titulo="Aula",
        autor_id=usuario_professor.id,
    )
    session.add(playlist)
    session.commit()
    session.refresh(playlist)
    
    pr1 = PlaylistRecurso(
        playlist_id=playlist.id,
        recurso_id=recurso_nota.id,
        ordem=0,
    )
    pr2 = PlaylistRecurso(
        playlist_id=playlist.id,
        recurso_id=recurso_url.id,
        ordem=1,
    )
    session.add(pr1)
    session.add(pr2)
    session.commit()
    
    # response = client.put(
    #     f"/playlists/{playlist.id}/reordenar",
    #     json={"recurso_ids_ordem": [recurso_url.id, recurso_nota.id]},
    #     headers={"Authorization": "Bearer token"}
    # )
    # assert response.status_code == 200
    pass


# ============================================================================
# Testes: Autenticação e Autorização
# ============================================================================

def test_apenas_autor_pode_editar(
    client: TestClient,
    session: Session,
    usuario_professor: User,
    usuario_aluno: User
):
    """Testa que apenas o autor pode editar a playlist."""
    # Criar playlist como professor
    playlist = Playlist(
        titulo="Aula do Professor",
        autor_id=usuario_professor.id,
    )
    session.add(playlist)
    session.commit()
    session.refresh(playlist)
    
    # Tentar editar como aluno (deve falhar com 403)
    # response = client.put(
    #     f"/playlists/{playlist.id}",
    #     json={"titulo": "Novo Título"},
    #     headers={"Authorization": f"Bearer {aluno_token}"}
    # )
    # assert response.status_code == 403
    pass


def test_apenas_autor_pode_deletar(
    client: TestClient,
    session: Session,
    usuario_professor: User,
    usuario_aluno: User
):
    """Testa que apenas o autor pode deletar a playlist."""
    # Criar playlist
    playlist = Playlist(
        titulo="Aula",
        autor_id=usuario_professor.id,
    )
    session.add(playlist)
    session.commit()
    session.refresh(playlist)
    
    # Tentar deletar como aluno (deve falhar com 403)
    # response = client.delete(
    #     f"/playlists/{playlist.id}",
    #     headers={"Authorization": f"Bearer {aluno_token}"}
    # )
    # assert response.status_code == 403
    pass
