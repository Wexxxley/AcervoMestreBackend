"""
Testes para CRUD de recursos.
"""
from http import HTTPStatus
import pytest
from app.enums.visibilidade import Visibilidade
from app.enums.estrutura_recurso import EstruturaRecurso


@pytest.mark.asyncio
async def test_get_all_recursos_public(client):
    """Deve listar recursos públicos sem autenticação."""
    response = await client.get('/recursos/get_all?page=1&per_page=10')
    
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert 'items' in data
    assert 'total' in data
    assert 'page' in data


@pytest.mark.asyncio
async def test_get_all_recursos_with_filters(client, recurso):
    """Deve filtrar recursos por palavra-chave."""
    response = await client.get(
        f'/recursos/get_all?palavra_chave={recurso.titulo[:5]}'
    )
    
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['total'] >= 1


@pytest.mark.asyncio
async def test_get_recurso_by_id_public(client, recurso):
    """Deve retornar recurso público por ID sem autenticação."""
    response = await client.get(f'/recursos/get/{recurso.id}')
    
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['id'] == recurso.id
    assert data['titulo'] == recurso.titulo


@pytest.mark.asyncio
async def test_get_recurso_privado_sem_autenticacao(client, recurso_privado):
    """Não deve retornar recurso privado sem autenticação."""
    response = await client.get(f'/recursos/get/{recurso_privado.id}')
    
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_get_recurso_privado_como_aluno(client, recurso_privado, aluno_token):
    """Aluno não deve acessar recurso privado."""
    response = await client.get(
        f'/recursos/get/{recurso_privado.id}',
        headers={'Authorization': f'Bearer {aluno_token}'},
    )
    
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_get_recurso_privado_como_professor(client, recurso_privado, token):
    """Professor deve acessar recurso privado."""
    response = await client.get(
        f'/recursos/get/{recurso_privado.id}',
        headers={'Authorization': f'Bearer {token}'},
    )
    
    assert response.status_code == HTTPStatus.OK


@pytest.mark.asyncio
async def test_create_recurso_nota(client, token):
    """Deve criar recurso tipo NOTA."""
    response = await client.post(
        '/recursos/create',
        headers={'Authorization': f'Bearer {token}'},
        data={
            'titulo': 'Recurso Teste',
            'descricao': 'Descrição teste',
            'estrutura': 'NOTA',
            'visibilidade': 'PUBLICO',
            'conteudo_markdown': '# Teste\n\nConteúdo de teste',
        },
    )
    
    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data['titulo'] == 'Recurso Teste'
    assert data['estrutura'] == 'NOTA'


@pytest.mark.asyncio
async def test_create_recurso_url(client, token):
    """Deve criar recurso tipo URL."""
    response = await client.post(
        '/recursos/create',
        headers={'Authorization': f'Bearer {token}'},
        data={
            'titulo': 'Link Teste',
            'descricao': 'Link externo',
            'estrutura': 'URL',
            'visibilidade': 'PUBLICO',
            'url_externa': 'https://example.com',
        },
    )
    
    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data['estrutura'] == 'URL'
    assert data['url_externa'] == 'https://example.com'


@pytest.mark.asyncio
async def test_create_recurso_without_auth(client):
    """Não deve criar recurso sem autenticação."""
    response = await client.post(
        '/recursos/create',
        data={
            'titulo': 'Tentativa',
            'descricao': 'Teste',
            'estrutura': 'NOTA',
            'conteudo_markdown': 'teste',
        },
    )
    
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_update_recurso_as_author(client, recurso, token):
    """Autor deve atualizar seu recurso."""
    response = await client.patch(
        f'/recursos/patch/{recurso.id}',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'titulo': 'Título Atualizado',
        },
    )
    
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['titulo'] == 'Título Atualizado'


@pytest.mark.asyncio
async def test_update_recurso_not_author(client, recurso, session, other_user):
    """Não-autor não deve atualizar recurso (exceto Coordenador)."""
    from app.core.security import create_access_token
    other_token = create_access_token(other_user.id)
    
    response = await client.patch(
        f'/recursos/patch/{recurso.id}',
        headers={'Authorization': f'Bearer {other_token}'},
        json={
            'titulo': 'Tentativa Atualizar',
        },
    )
    
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_update_recurso_as_coordenador(client, recurso, coordenador_token):
    """Coordenador deve atualizar qualquer recurso."""
    response = await client.patch(
        f'/recursos/patch/{recurso.id}',
        headers={'Authorization': f'Bearer {coordenador_token}'},
        json={
            'descricao': 'Atualizado pelo Coordenador',
        },
    )
    
    assert response.status_code == HTTPStatus.OK


@pytest.mark.asyncio
async def test_delete_recurso_as_author(client, recurso, token):
    """Autor deve deletar seu recurso."""
    response = await client.delete(
        f'/recursos/delete/{recurso.id}',
        headers={'Authorization': f'Bearer {token}'},
    )
    
    assert response.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.asyncio
async def test_delete_recurso_not_author(client, recurso, session, other_user):
    """Não-autor não deve deletar recurso (exceto Coordenador)."""
    from app.core.security import create_access_token
    other_token = create_access_token(other_user.id)
    
    response = await client.delete(
        f'/recursos/delete/{recurso.id}',
        headers={'Authorization': f'Bearer {other_token}'},
    )
    
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.asyncio
async def test_incrementa_visualizacoes(client, recurso):
    """Deve incrementar contador de visualizações."""
    views_antes = recurso.visualizacoes
    
    await client.get(f'/recursos/get/{recurso.id}')
    
    response = await client.get(f'/recursos/get/{recurso.id}')
    data = response.json()
    
    assert data['visualizacoes'] > views_antes
