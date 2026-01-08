"""
Testes para playlists.
"""
from http import HTTPStatus
import pytest


@pytest.mark.asyncio
async def test_create_playlist(client, token):
    """Deve criar playlist."""
    # Rota corrigida: /playlists/create
    response = await client.post(
        '/playlists/create',
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
    # Rota corrigida: /playlists/create
    response = await client.post(
        '/playlists/create',
        json={
            'titulo': 'Tentativa Playlist',
        },
    )
    
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_playlist_by_id(client, playlist):
    """Deve retornar playlist por ID."""
    # Rota corrigida: /playlists/get/{id}
    response = await client.get(f'/playlists/get/{playlist.id}')
    
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['id'] == playlist.id
    assert data['titulo'] == playlist.titulo


@pytest.mark.asyncio
async def test_list_playlists(client, playlist):
    """Deve listar playlists."""
    # Rota corrigida: /playlists/get_all
    response = await client.get('/playlists/get_all?page=1&per_page=10')
    
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['total'] >= 1


@pytest.mark.asyncio
async def test_update_playlist_as_author(client, playlist, token):
    """Autor deve atualizar playlist."""
    # Rota corrigida: /playlists/update/{id}
    response = await client.put(
        f'/playlists/update/{playlist.id}',
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
    
    # Rota corrigida: /playlists/update/{id}
    response = await client.put(
        f'/playlists/update/{playlist.id}',
        headers={'Authorization': f'Bearer {other_token}'},
        json={
            'titulo': 'Tentativa',
        },
    )
    
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_delete_playlist_as_author(client, playlist, token):
    """Autor deve deletar playlist."""
    # Rota corrigida: /playlists/delete/{id}
    response = await client.delete(
        f'/playlists/delete/{playlist.id}',
        headers={'Authorization': f'Bearer {token}'},
    )
    
    assert response.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.asyncio
async def test_add_recurso_to_playlist(client, playlist, recurso, token):
    """Deve adicionar recurso à playlist."""
    # Rota corrigida: /playlists/add_recurso/{id}
    response = await client.post(
        f'/playlists/add_recurso/{playlist.id}',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'recurso_id': recurso.id,
        },
    )
    
    assert response.status_code == HTTPStatus.CREATED


@pytest.mark.asyncio
async def test_add_recurso_duplicate(client, playlist, recurso, token):
    """Não deve adicionar recurso duplicado."""
    # Rota corrigida: /playlists/add_recurso/{id}
    
    # Adicionar primeira vez
    await client.post(
        f'/playlists/add_recurso/{playlist.id}',
        headers={'Authorization': f'Bearer {token}'},
        json={'recurso_id': recurso.id},
    )
    
    # Tentar adicionar novamente
    response = await client.post(
        f'/playlists/add_recurso/{playlist.id}',
        headers={'Authorization': f'Bearer {token}'},
        json={'recurso_id': recurso.id},
    )
    
    assert response.status_code == HTTPStatus.CONFLICT


@pytest.mark.asyncio
async def test_remove_recurso_from_playlist(client, playlist, recurso, token):
    """Deve remover recurso da playlist."""
    # Adicionar recurso primeiro
    await client.post(
        f'/playlists/add_recurso/{playlist.id}',
        headers={'Authorization': f'Bearer {token}'},
        json={'recurso_id': recurso.id},
    )
    
    # Rota corrigida: /playlists/delete_recurso/{playlist_id}/{recurso_id}
    response = await client.delete(
        f'/playlists/delete_recurso/{playlist.id}/{recurso.id}',
        headers={'Authorization': f'Bearer {token}'},
    )
    
    assert response.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.asyncio
async def test_get_playlist_not_found(client):
    """Deve retornar 404 para playlist inexistente."""
    # Rota corrigida: /playlists/get/{id}
    response = await client.get('/playlists/get/99999')
    
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_list_playlists_with_filter(client, playlist, token, session):
    """Deve filtrar playlists por autor_id."""
    # Rota corrigida: /playlists/get_all
    response = await client.get(f'/playlists/get_all?autor_id={playlist.autor_id}&page=1&per_page=10')
    
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['total'] >= 1
    for item in data['items']:
        assert item['autor_id'] == playlist.autor_id


@pytest.mark.asyncio
async def test_update_playlist_without_fields(client, playlist, token):
    """Não deve atualizar playlist sem campos."""
    # Rota corrigida: /playlists/update/{id}
    response = await client.put(
        f'/playlists/update/{playlist.id}',
        headers={'Authorization': f'Bearer {token}'},
        json={},
    )
    
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.asyncio
async def test_update_playlist_only_description(client, playlist, token):
    """Deve atualizar apenas descrição da playlist."""
    # Rota corrigida: /playlists/update/{id}
    response = await client.put(
        f'/playlists/update/{playlist.id}',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'descricao': 'Nova descrição',
        },
    )
    
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['descricao'] == 'Nova descrição'
    assert data['titulo'] == playlist.titulo


@pytest.mark.asyncio
async def test_update_playlist_not_found(client, token):
    """Deve retornar 404 ao atualizar playlist inexistente."""
    # Rota corrigida: /playlists/update/{id}
    response = await client.put(
        '/playlists/update/99999',
        headers={'Authorization': f'Bearer {token}'},
        json={'titulo': 'Teste'},
    )
    
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_delete_playlist_not_author(client, playlist, other_user):
    """Não-autor não deve deletar playlist."""
    from app.core.security import create_access_token
    other_token = create_access_token(other_user.id)
    
    # Rota corrigida: /playlists/delete/{id}
    response = await client.delete(
        f'/playlists/delete/{playlist.id}',
        headers={'Authorization': f'Bearer {other_token}'},
    )
    
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_delete_playlist_not_found(client, token):
    """Deve retornar 404 ao deletar playlist inexistente."""
    # Rota corrigida: /playlists/delete/{id}
    response = await client.delete(
        '/playlists/delete/99999',
        headers={'Authorization': f'Bearer {token}'},
    )
    
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_add_recurso_not_found(client, playlist, token):
    """Deve retornar 404 ao adicionar recurso inexistente."""
    # Rota corrigida: /playlists/add_recurso/{id}
    response = await client.post(
        f'/playlists/add_recurso/{playlist.id}',
        headers={'Authorization': f'Bearer {token}'},
        json={'recurso_id': 99999},
    )
    
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_add_recurso_playlist_not_found(client, recurso, token):
    """Deve retornar 404 ao adicionar recurso em playlist inexistente."""
    # Rota corrigida: /playlists/add_recurso/{id}
    response = await client.post(
        '/playlists/add_recurso/99999',
        headers={'Authorization': f'Bearer {token}'},
        json={'recurso_id': recurso.id},
    )
    
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_add_recurso_not_author(client, playlist, recurso, other_user):
    """Não-autor não deve adicionar recurso."""
    from app.core.security import create_access_token
    other_token = create_access_token(other_user.id)
    
    # Rota corrigida: /playlists/add_recurso/{id}
    response = await client.post(
        f'/playlists/add_recurso/{playlist.id}',
        headers={'Authorization': f'Bearer {other_token}'},
        json={'recurso_id': recurso.id},
    )
    
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_remove_recurso_not_in_playlist(client, playlist, recurso, token):
    """Deve retornar 404 ao remover recurso que não está na playlist."""
    # Rota corrigida: /playlists/delete_recurso/{playlist_id}/{recurso_id}
    response = await client.delete(
        f'/playlists/delete_recurso/{playlist.id}/{recurso.id}',
        headers={'Authorization': f'Bearer {token}'},
    )
    
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_remove_recurso_not_author(client, playlist, recurso, token, other_user):
    """Não-autor não deve remover recurso."""
    # Adicionar recurso como autor
    await client.post(
        f'/playlists/add_recurso/{playlist.id}',
        headers={'Authorization': f'Bearer {token}'},
        json={'recurso_id': recurso.id},
    )
    
    from app.core.security import create_access_token
    other_token = create_access_token(other_user.id)
    
    # Rota corrigida: /playlists/delete_recurso/{playlist_id}/{recurso_id}
    response = await client.delete(
        f'/playlists/delete_recurso/{playlist.id}/{recurso.id}',
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
    
    # Adicionar à playlist
    for idx, r in enumerate(recursos):
        await session.refresh(r)
        pr = PlaylistRecurso(
            playlist_id=playlist.id,
            recurso_id=r.id,
            ordem=idx
        )
        session.add(pr)
    
    await session.commit()
    
    # Rota corrigida: /playlists/update/{id}/reordenar
    nova_ordem = [r.id for r in reversed(recursos)]
    response = await client.put(
        f'/playlists/update/{playlist.id}/reordenar',
        headers={'Authorization': f'Bearer {token}'},
        json={'recurso_ids_ordem': nova_ordem},
    )
    
    assert response.status_code == HTTPStatus.OK


@pytest.mark.asyncio
async def test_reorder_recursos_empty_list(client, playlist, token):
    """Não deve reordenar com lista vazia."""
    # Rota corrigida: /playlists/update/{id}/reordenar
    response = await client.put(
        f'/playlists/update/{playlist.id}/reordenar',
        headers={'Authorization': f'Bearer {token}'},
        json={'recurso_ids_ordem': []},
    )
    
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.asyncio
async def test_reorder_recursos_duplicates(client, playlist, recurso, token):
    """Não deve reordenar com IDs duplicados."""
    await client.post(
        f'/playlists/add_recurso/{playlist.id}',
        headers={'Authorization': f'Bearer {token}'},
        json={'recurso_id': recurso.id},
    )
    
    # Rota corrigida: /playlists/update/{id}/reordenar
    response = await client.put(
        f'/playlists/update/{playlist.id}/reordenar',
        headers={'Authorization': f'Bearer {token}'},
        json={'recurso_ids_ordem': [recurso.id, recurso.id]},
    )
    
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.asyncio
async def test_reorder_recursos_not_in_playlist(client, playlist, recurso, token):
    """Não deve reordenar com recurso que não está na playlist."""
    # Rota corrigida: /playlists/update/{id}/reordenar
    response = await client.put(
        f'/playlists/update/{playlist.id}/reordenar',
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
    
    for idx, r in enumerate(recursos):
        await session.refresh(r)
        pr = PlaylistRecurso(
            playlist_id=playlist.id,
            recurso_id=r.id,
            ordem=idx
        )
        session.add(pr)
    
    await session.commit()
    
    # Rota corrigida: /playlists/update/{id}/reordenar
    response = await client.put(
        f'/playlists/update/{playlist.id}/reordenar',
        headers={'Authorization': f'Bearer {token}'},
        json={'recurso_ids_ordem': [recursos[0].id]},
    )
    
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.asyncio
async def test_reorder_recursos_not_author(client, playlist, recurso, token, other_user):
    """Não-autor não deve reordenar recursos."""
    await client.post(
        f'/playlists/add_recurso/{playlist.id}',
        headers={'Authorization': f'Bearer {token}'},
        json={'recurso_id': recurso.id},
    )
    
    from app.core.security import create_access_token
    other_token = create_access_token(other_user.id)
    
    # Rota corrigida: /playlists/update/{id}/reordenar
    response = await client.put(
        f'/playlists/update/{playlist.id}/reordenar',
        headers={'Authorization': f'Bearer {other_token}'},
        json={'recurso_ids_ordem': [recurso.id]},
    )
    
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_reorder_recursos_not_found(client, token):
    """Deve retornar 404 ao reordenar playlist inexistente."""
    # Rota corrigida: /playlists/update/{id}/reordenar
    response = await client.put(
        '/playlists/update/99999/reordenar',
        headers={'Authorization': f'Bearer {token}'},
        json={'recurso_ids_ordem': [1]},
    )
    
    assert response.status_code == HTTPStatus.NOT_FOUND