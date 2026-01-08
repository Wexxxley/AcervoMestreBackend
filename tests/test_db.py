"""
Testes para operações com banco de dados.
"""
from datetime import datetime
import pytest
from sqlmodel import select
from app.models.user import User
from app.models.recurso import Recurso
from app.enums.perfil import Perfil
from app.enums.status import Status

@pytest.mark.asyncio
async def test_create_user_in_db(session, mock_db_time):
    """Deve criar usuário no banco com timestamps."""
    async with mock_db_time(model=User, time=datetime(2024, 1, 1)) as time:
        from app.core.security import get_password_hash
        
        new_user = User(
            nome='Test User DB',
            email='testdb@test.com',
            perfil=Perfil.Professor,
            status=Status.Ativo,
            senha_hash=get_password_hash('senha123'),
        )
        
        session.add(new_user)
        await session.commit()
    
    # Verificar se foi criado
    statement = select(User).where(User.email == 'testdb@test.com')
    result = await session.execute(statement)
    user = result.scalar_one()
    
    assert user.nome == 'Test User DB'
    assert user.email == 'testdb@test.com'
    assert user.perfil == Perfil.Professor
    assert user.criado_em == time


@pytest.mark.asyncio
async def test_create_recurso_in_db(session, user, mock_db_time):
    """Deve criar recurso no banco com timestamps."""
    async with mock_db_time(model=Recurso, time=datetime(2024, 1, 1)) as time:
        from app.enums.visibilidade import Visibilidade
        from app.enums.estrutura_recurso import EstruturaRecurso
        
        new_recurso = Recurso(
            titulo='Recurso DB Test',
            descricao='Teste de banco',
            visibilidade=Visibilidade.PUBLICO,
            estrutura=EstruturaRecurso.NOTA,
            conteudo_markdown='# Teste',
            autor_id=user.id,
        )
        
        session.add(new_recurso)
        await session.commit()
    
    # Verificar se foi criado
    statement = select(Recurso).where(Recurso.titulo == 'Recurso DB Test')
    result = await session.execute(statement)
    recurso = result.scalar_one()
    
    assert recurso.titulo == 'Recurso DB Test'
    assert recurso.autor_id == user.id
    assert recurso.criado_em == time


@pytest.mark.asyncio
async def test_user_relationship_with_recursos(session, user):
    """Deve manter relacionamento entre User e Recursos."""
    from app.enums.visibilidade import Visibilidade
    from app.enums.estrutura_recurso import EstruturaRecurso
    
    # Criar vários recursos
    for i in range(3):
        recurso = Recurso(
            titulo=f'Recurso {i}',
            descricao=f'Descrição {i}',
            visibilidade=Visibilidade.PUBLICO,
            estrutura=EstruturaRecurso.NOTA,
            conteudo_markdown=f'# Conteúdo {i}',
            autor_id=user.id,
        )
        session.add(recurso)
    
    await session.commit()
    
    # Verificar quantos recursos o usuário tem
    statement = select(Recurso).where(Recurso.autor_id == user.id)
    result = await session.execute(statement)
    recursos = result.scalars().all()
    
    assert len(recursos) == 3

@pytest.mark.asyncio
async def test_delete_cascade_behavior(session, user):
    """Deve testar comportamento FK RESTRICT ao deletar usuário com recursos."""
    from app.enums.visibilidade import Visibilidade
    from app.enums.estrutura_recurso import EstruturaRecurso
    from sqlalchemy.exc import IntegrityError
    import pytest
    
    # Criar recurso associado ao usuário
    recurso = Recurso(
        titulo='Recurso para teste de deleção',
        descricao='Teste',
        visibilidade=Visibilidade.PUBLICO,
        estrutura=EstruturaRecurso.NOTA,
        conteudo_markdown='# Teste',
        autor_id=user.id,
    )
    session.add(recurso)
    await session.commit()
    
    # Tentar deletar usuário deve falhar devido a FK RESTRICT
    # pois ainda existe um recurso referenciando este usuário
    with pytest.raises(IntegrityError) as exc_info:
        await session.delete(user)
        await session.commit()
    
    # Verificar que a mensagem de erro menciona a constraint
    assert 'fk_recurso_autor_id' in str(exc_info.value).lower()