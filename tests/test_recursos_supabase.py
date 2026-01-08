"""
Testes para upload de recursos usando Supabase Storage.
"""
from http import HTTPStatus
import pytest
from io import BytesIO


@pytest.mark.asyncio
async def test_create_recurso_upload_supabase(client, token):
    """Deve criar recurso com upload para Supabase."""
    # Criar arquivo fake para upload
    file_content = b"PDF fake content for testing"
    file = BytesIO(file_content)
    
    response = await client.post(
        '/recursos/upload/supabase',
        headers={'Authorization': f'Bearer {token}'},
        data={
            'titulo': 'Apostila Python - Supabase',
            'descricao': 'Material de Python armazenado no Supabase',
            'visibilidade': 'PUBLICO',
            'is_destaque': 'true',
        },
        files={
            'arquivo': ('apostila.pdf', file, 'application/pdf')
        }
    )
    
    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data['titulo'] == 'Apostila Python - Supabase'
    assert data['estrutura'] == 'UPLOAD'
    assert data['storage_key'].startswith('http')  # Deve ser URL do Supabase
    assert data['mime_type'] == 'application/pdf'
    assert data['tamanho_bytes'] == len(file_content)


@pytest.mark.asyncio
async def test_create_recurso_upload_supabase_sem_arquivo(client, token):
    """Deve falhar ao tentar criar recurso sem arquivo."""
    response = await client.post(
        '/recursos/upload/supabase',
        headers={'Authorization': f'Bearer {token}'},
        data={
            'titulo': 'Recurso sem arquivo',
            'descricao': 'Teste de validação',
            'visibilidade': 'PUBLICO',
        }
    )
    
    # Deve retornar erro 422 (campo obrigatório faltando)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_create_recurso_upload_supabase_tipo_invalido(client, token):
    """Deve rejeitar arquivo com tipo não permitido."""
    file_content = b"Executable fake content"
    file = BytesIO(file_content)
    
    response = await client.post(
        '/recursos/upload/supabase',
        headers={'Authorization': f'Bearer {token}'},
        data={
            'titulo': 'Arquivo Inválido',
            'descricao': 'Teste de validação de tipo',
            'visibilidade': 'PUBLICO',
        },
        files={
            'arquivo': ('virus.exe', file, 'application/x-msdownload')
        }
    )
    
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert 'não permitido' in response.json()['detail'].lower()


@pytest.mark.asyncio
async def test_download_recurso_supabase(client, db_session, token):
    """Deve fazer download de recurso do Supabase."""
    from app.models.recurso import Recurso
    from app.enums.estrutura_recurso import EstruturaRecurso
    from app.enums.visibilidade import Visibilidade
    
    # Criar recurso fake com URL do Supabase
    recurso = Recurso(
        titulo="Recurso Supabase",
        descricao="Teste de download",
        estrutura=EstruturaRecurso.UPLOAD,
        visibilidade=Visibilidade.PUBLICO,
        autor_id=1,
        storage_key="https://projeto.supabase.co/storage/v1/object/public/recursos/abc123.pdf",
        mime_type="application/pdf",
        tamanho_bytes=1024
    )
    db_session.add(recurso)
    await db_session.commit()
    await db_session.refresh(recurso)
    
    response = await client.post(
        f'/recursos/{recurso.id}/download',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['download_url'].startswith('http')
    assert 'supabase' in data['download_url']


@pytest.mark.asyncio
async def test_delete_recurso_supabase(client, db_session, token):
    """Deve deletar recurso e arquivo do Supabase."""
    from app.models.recurso import Recurso
    from app.enums.estrutura_recurso import EstruturaRecurso
    from app.enums.visibilidade import Visibilidade
    
    # Criar recurso fake com URL do Supabase
    recurso = Recurso(
        titulo="Recurso para Deletar",
        descricao="Teste de deleção",
        estrutura=EstruturaRecurso.UPLOAD,
        visibilidade=Visibilidade.PUBLICO,
        autor_id=1,
        storage_key="https://projeto.supabase.co/storage/v1/object/public/recursos/delete-test.pdf",
        mime_type="application/pdf",
        tamanho_bytes=1024
    )
    db_session.add(recurso)
    await db_session.commit()
    await db_session.refresh(recurso)
    
    response = await client.delete(
        f'/recursos/delete/{recurso.id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    assert response.status_code == HTTPStatus.NO_CONTENT
