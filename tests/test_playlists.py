"""
Testes para playlists.
"""
from http import HTTPStatus
import pytest


@pytest.mark.asyncio
async def test_create_playlist(client, token):
    """Deve criar playlist."""
    response = await client.post(
        '/playlists/',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'titulo': 'Minha Playlist',
            'descricao': 'Descrição da playlist',
        },
    )
    
    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data['titulo'] == 'Minha Playlist'


@pytest.mark.asyncio
async def test_create_playlist_without_auth(client):
    """Não deve criar playlist sem autenticação."""
    response = await client.post(
        '/playlists/',
        json={
            'titulo': 'Tentativa Playlist',
        },
    )
    
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_playlist_by_id(client, playlist):
    """Deve retornar playlist por ID."""
    response = await client.get(f'/playlists/{playlist.id}')
    
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['id'] == playlist.id
    assert data['titulo'] == playlist.titulo


@pytest.mark.asyncio
async def test_list_playlists(client, playlist):
    """Deve listar playlists."""
    response = await client.get('/playlists?page=1&per_page=10')
    
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['total'] >= 1


@pytest.mark.asyncio
async def test_update_playlist_as_author(client, playlist, token):
    """Autor deve atualizar playlist."""
    response = await client.put(
        f'/playlists/{playlist.id}',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'titulo': 'Título Atualizado',
        },
    )
    
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['titulo'] == 'Título Atualizado'


@pytest.mark.asyncio
async def test_update_playlist_not_author(client, playlist, session, other_user):
    """Não-autor não deve atualizar playlist."""
    from app.core.security import create_access_token
    other_token = create_access_token(other_user.id)
    
    response = await client.put(
        f'/playlists/{playlist.id}',
        headers={'Authorization': f'Bearer {other_token}'},
        json={
            'titulo': 'Tentativa',
        },
    )
    
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_delete_playlist_as_author(client, playlist, token):
    """Autor deve deletar playlist."""
    response = await client.delete(
        f'/playlists/{playlist.id}',
        headers={'Authorization': f'Bearer {token}'},
    )
    
    assert response.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.asyncio
async def test_add_recurso_to_playlist(client, playlist, recurso, token):
    """Deve adicionar recurso à playlist."""
    response = await client.post(
        f'/playlists/{playlist.id}/recursos',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'recurso_id': recurso.id,
        },
    )
    
    assert response.status_code == HTTPStatus.CREATED


@pytest.mark.asyncio
async def test_add_recurso_duplicate(client, playlist, recurso, token):
    """Não deve adicionar recurso duplicado."""
    # Adicionar primeira vez
    await client.post(
        f'/playlists/{playlist.id}/recursos',
        headers={'Authorization': f'Bearer {token}'},
        json={'recurso_id': recurso.id},
    )
    
    # Tentar adicionar novamente
    response = await client.post(
        f'/playlists/{playlist.id}/recursos',
        headers={'Authorization': f'Bearer {token}'},
        json={'recurso_id': recurso.id},
    )
    
    assert response.status_code == HTTPStatus.CONFLICT


@pytest.mark.asyncio
async def test_remove_recurso_from_playlist(client, playlist, recurso, token):
    """Deve remover recurso da playlist."""
    # Adicionar recurso
    await client.post(
        f'/playlists/{playlist.id}/recursos',
        headers={'Authorization': f'Bearer {token}'},
        json={'recurso_id': recurso.id},
    )
    
    # Remover recurso
    response = await client.delete(
        f'/playlists/{playlist.id}/recursos/{recurso.id}',
        headers={'Authorization': f'Bearer {token}'},
    )
    
    assert response.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.asyncio
async def test_get_playlist_not_found(client):
    """Deve retornar 404 para playlist inexistente."""
    response = await client.get('/playlists/99999')
    
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_list_playlists_with_filter(client, playlist, token, session):
    """Deve filtrar playlists por autor_id."""
    # Buscar playlists do autor da fixture
    response = await client.get(f'/playlists?autor_id={playlist.autor_id}&page=1&per_page=10')
    
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['total'] >= 1
    # Verificar que todos os itens são do mesmo autor
    for item in data['items']:
        assert item['autor_id'] == playlist.autor_id


@pytest.mark.asyncio
async def test_update_playlist_without_fields(client, playlist, token):
    """Não deve atualizar playlist sem campos."""
    response = await client.put(
        f'/playlists/{playlist.id}',
        headers={'Authorization': f'Bearer {token}'},
        json={},
    )
    
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.asyncio
async def test_update_playlist_only_description(client, playlist, token):
    """Deve atualizar apenas descrição da playlist."""
    response = await client.put(
        f'/playlists/{playlist.id}',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'descricao': 'Nova descrição',
        },
    )
    
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['descricao'] == 'Nova descrição'
    assert data['titulo'] == playlist.titulo  # Título não mudou


@pytest.mark.asyncio
async def test_update_playlist_not_found(client, token):
    """Deve retornar 404 ao atualizar playlist inexistente."""
    response = await client.put(
        '/playlists/99999',
        headers={'Authorization': f'Bearer {token}'},
        json={'titulo': 'Teste'},
    )
    
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_delete_playlist_not_author(client, playlist, other_user):
    """Não-autor não deve deletar playlist."""
    from app.core.security import create_access_token
    other_token = create_access_token(other_user.id)
    
    response = await client.delete(
        f'/playlists/{playlist.id}',
        headers={'Authorization': f'Bearer {other_token}'},
    )
    
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_delete_playlist_not_found(client, token):
    """Deve retornar 404 ao deletar playlist inexistente."""
    response = await client.delete(
        '/playlists/99999',
        headers={'Authorization': f'Bearer {token}'},
    )
    
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_add_recurso_not_found(client, playlist, token):
    """Deve retornar 404 ao adicionar recurso inexistente."""
    response = await client.post(
        f'/playlists/{playlist.id}/recursos',
        headers={'Authorization': f'Bearer {token}'},
        json={'recurso_id': 99999},
    )
    
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_add_recurso_playlist_not_found(client, recurso, token):
    """Deve retornar 404 ao adicionar recurso em playlist inexistente."""
    response = await client.post(
        '/playlists/99999/recursos',
        headers={'Authorization': f'Bearer {token}'},
        json={'recurso_id': recurso.id},
    )
    
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_add_recurso_not_author(client, playlist, recurso, other_user):
    """Não-autor não deve adicionar recurso."""
    from app.core.security import create_access_token
    other_token = create_access_token(other_user.id)
    
    response = await client.post(
        f'/playlists/{playlist.id}/recursos',
        headers={'Authorization': f'Bearer {other_token}'},
        json={'recurso_id': recurso.id},
    )
    
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_remove_recurso_not_in_playlist(client, playlist, recurso, token):
    """Deve retornar 404 ao remover recurso que não está na playlist."""
    response = await client.delete(
        f'/playlists/{playlist.id}/recursos/{recurso.id}',
        headers={'Authorization': f'Bearer {token}'},
    )
    
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_remove_recurso_not_author(client, playlist, recurso, token, other_user):
    """Não-autor não deve remover recurso."""
    # Adicionar recurso como autor
    await client.post(
        f'/playlists/{playlist.id}/recursos',
        headers={'Authorization': f'Bearer {token}'},
        json={'recurso_id': recurso.id},
    )
    
    # Tentar remover como outro usuário
    from app.core.security import create_access_token
    other_token = create_access_token(other_user.id)
    
    response = await client.delete(
        f'/playlists/{playlist.id}/recursos/{recurso.id}',
        headers={'Authorization': f'Bearer {other_token}'},
    )
    
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_reorder_recursos(client, playlist, session, token):
    """Deve reordenar recursos na playlist."""
    from app.models.playlist_recurso import PlaylistRecurso
    from app.enums.visibilidade import Visibilidade
    from app.enums.estrutura_recurso import EstruturaRecurso
    from app.models.recurso import Recurso
    
    # Criar recursos diretamente no banco
    recursos = []
    for i in range(3):
        r = Recurso(
            titulo=f'Recurso {i+1}',
            descricao='Teste',
            visibilidade=Visibilidade.PUBLICO,
            estrutura=EstruturaRecurso.NOTA,
            conteudo_markdown=f'# Content {i+1}',
            autor_id=playlist.autor_id
        )
        session.add(r)
        recursos.append(r)
    
    await session.commit()
    
    # Adicionar à playlist diretamente
    for idx, r in enumerate(recursos):
        await session.refresh(r)
        pr = PlaylistRecurso(
            playlist_id=playlist.id,
            recurso_id=r.id,
            ordem=idx
        )
        session.add(pr)
    
    await session.commit()
    
    # Reordenar (inverter ordem)
    nova_ordem = [r.id for r in reversed(recursos)]
    response = await client.put(
        f'/playlists/{playlist.id}/reordenar',
        headers={'Authorization': f'Bearer {token}'},
        json={'recurso_ids_ordem': nova_ordem},
    )
    
    assert response.status_code == HTTPStatus.OK


@pytest.mark.asyncio
async def test_reorder_recursos_empty_list(client, playlist, token):
    """Não deve reordenar com lista vazia."""
    response = await client.put(
        f'/playlists/{playlist.id}/reordenar',
        headers={'Authorization': f'Bearer {token}'},
        json={'recurso_ids_ordem': []},
    )
    
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.asyncio
async def test_reorder_recursos_duplicates(client, playlist, recurso, token):
    """Não deve reordenar com IDs duplicados."""
    # Adicionar recurso
    await client.post(
        f'/playlists/{playlist.id}/recursos',
        headers={'Authorization': f'Bearer {token}'},
        json={'recurso_id': recurso.id},
    )
    
    response = await client.put(
        f'/playlists/{playlist.id}/reordenar',
        headers={'Authorization': f'Bearer {token}'},
        json={'recurso_ids_ordem': [recurso.id, recurso.id]},
    )
    
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.asyncio
async def test_reorder_recursos_not_in_playlist(client, playlist, recurso, token):
    """Não deve reordenar com recurso que não está na playlist."""
    response = await client.put(
        f'/playlists/{playlist.id}/reordenar',
        headers={'Authorization': f'Bearer {token}'},
        json={'recurso_ids_ordem': [recurso.id]},
    )
    
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.asyncio
async def test_reorder_recursos_incomplete_list(client, playlist, session, token):
    """Não deve reordenar se a lista não contém todos os recursos."""
    from app.models.playlist_recurso import PlaylistRecurso
    from app.enums.visibilidade import Visibilidade
    from app.enums.estrutura_recurso import EstruturaRecurso
    from app.models.recurso import Recurso
    
    # Criar 2 recursos
    recursos = []
    for i in range(2):
        r = Recurso(
            titulo=f'Recurso {i+1}',
            descricao='Teste',
            visibilidade=Visibilidade.PUBLICO,
            estrutura=EstruturaRecurso.NOTA,
            conteudo_markdown=f'# Content {i+1}',
            autor_id=playlist.autor_id
        )
        session.add(r)
        recursos.append(r)
    
    await session.commit()
    
    # Adicionar à playlist diretamente
    for idx, r in enumerate(recursos):
        await session.refresh(r)
        pr = PlaylistRecurso(
            playlist_id=playlist.id,
            recurso_id=r.id,
            ordem=idx
        )
        session.add(pr)
    
    await session.commit()
    
    # Tentar reordenar com apenas 1 recurso
    response = await client.put(
        f'/playlists/{playlist.id}/reordenar',
        headers={'Authorization': f'Bearer {token}'},
        json={'recurso_ids_ordem': [recursos[0].id]},
    )
    
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.asyncio
async def test_reorder_recursos_not_author(client, playlist, recurso, token, other_user):
    """Não-autor não deve reordenar recursos."""
    # Adicionar recurso como autor
    await client.post(
        f'/playlists/{playlist.id}/recursos',
        headers={'Authorization': f'Bearer {token}'},
        json={'recurso_id': recurso.id},
    )
    
    # Tentar reordenar como outro usuário
    from app.core.security import create_access_token
    other_token = create_access_token(other_user.id)
    
    response = await client.put(
        f'/playlists/{playlist.id}/reordenar',
        headers={'Authorization': f'Bearer {other_token}'},
        json={'recurso_ids_ordem': [recurso.id]},
    )
    
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_reorder_recursos_not_found(client, token):
    """Deve retornar 404 ao reordenar playlist inexistente."""
    response = await client.put(
        '/playlists/99999/reordenar',
        headers={'Authorization': f'Bearer {token}'},
        json={'recurso_ids_ordem': [1]},
    )
    
    assert response.status_code == HTTPStatus.NOT_FOUND
