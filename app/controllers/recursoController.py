from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import func, or_, update
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.dtos.recursoDtos import RecursoCreate, RecursoRead, RecursoUpdate
from app.models.recurso import Recurso
from app.models.user import User
from app.core.database import get_session
from app.core.security import get_current_user
from app.enums.visibilidade import Visibilidade
from app.enums.perfil import Perfil
from app.utils.pagination import PaginationParams, PaginatedResponse

recurso_router = APIRouter(prefix="/recursos", tags=["Recursos"])

@recurso_router.get("/get/{recurso_id}", response_model=RecursoRead)
async def get_recurso_by_id(
    recurso_id: int, 
    session: AsyncSession = Depends(get_session),
    current_user: User | None = Depends(get_current_user)
):
    # Primeiro, incrementar visualizações atomicamente
    await session.execute(
        update(Recurso)
        .where(Recurso.id == recurso_id)
        .values(visualizacoes=Recurso.visualizacoes + 1)
    )
    
    # Depois buscar o recurso atualizado
    statement = select(Recurso).where(Recurso.id == recurso_id)
    result = await session.exec(statement)
    recurso = result.first()
    
    if not recurso:
        raise HTTPException(status_code=404, detail="Recurso não encontrado")
    
    # Verificar permissões de visibilidade
    if recurso.visibilidade == Visibilidade.PRIVADO:
        # Recursos privados só podem ser vistos por usuários que NÃO são ALUNO
        if not current_user or current_user.perfil == Perfil.Aluno:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Acesso negado a recurso privado"
            )
    
    await session.commit()
    
    return recurso


@recurso_router.get("/get_all", response_model=PaginatedResponse[RecursoRead])
async def get_all_recursos(
    session: AsyncSession = Depends(get_session),
    pagination: PaginationParams = Depends(),
    palavra_chave: str | None = Query(None, description="Busca por título ou descrição"),
    estrutura: str | None = Query(None, description="Filtra por estrutura (UPLOAD, URL, NOTA)"),
):
    # Montar a query base
    statement = select(Recurso)
    
    # Filtro por palavra-chave
    if palavra_chave:
        statement = statement.where(
            or_(
                Recurso.titulo.ilike(f"%{palavra_chave}%"),
                Recurso.descricao.ilike(f"%{palavra_chave}%")
            )
        )
    
    # Filtro por estrutura
    if estrutura:
        statement = statement.where(Recurso.estrutura == estrutura)

    # Contar o total de registros
    count_statement = select(func.count()).select_from(Recurso)
    
    if palavra_chave:
        count_statement = count_statement.where(
            or_(
                Recurso.titulo.ilike(f"%{palavra_chave}%"),
                Recurso.descricao.ilike(f"%{palavra_chave}%")
            )
        )
    
    if estrutura:
        count_statement = count_statement.where(Recurso.estrutura == estrutura)
        
    total_result = await session.exec(count_statement)
    total_items = total_result.one()

    # Aplicar a paginação
    offset = (pagination.page - 1) * pagination.per_page
    statement = statement.offset(offset).limit(pagination.per_page).order_by(Recurso.criado_em.desc())
    
    result = await session.exec(statement)
    recursos = result.all()

    # Calcular total de páginas
    total_pages = (total_items + pagination.per_page - 1) // pagination.per_page

    return PaginatedResponse(
        items=recursos,
        total=total_items,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=total_pages
    )


@recurso_router.post("/create", response_model=RecursoRead, status_code=status.HTTP_201_CREATED)
async def create_recurso(recurso_in: RecursoCreate, session: AsyncSession = Depends(get_session)):
    recurso_dict = recurso_in.model_dump()
    db_recurso = Recurso.model_validate(recurso_dict)
    
    session.add(db_recurso)
    await session.commit()
    await session.refresh(db_recurso)
        
    return db_recurso


@recurso_router.patch("/patch/{recurso_id}", response_model=RecursoRead)
async def update_recurso(
    recurso_id: int, 
    recurso_input: RecursoUpdate, 
    session: AsyncSession = Depends(get_session)
):
    statement = select(Recurso).where(Recurso.id == recurso_id)
    result = await session.exec(statement)
    db_recurso = result.first()

    if not db_recurso:
        raise HTTPException(status_code=404, detail="Recurso não encontrado")

    recurso_data = recurso_input.model_dump(exclude_unset=True)

    for key, value in recurso_data.items():
        setattr(db_recurso, key, value)

    session.add(db_recurso)
    await session.commit()
    await session.refresh(db_recurso)
    return db_recurso


@recurso_router.delete("/delete/{recurso_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recurso(recurso_id: int, session: AsyncSession = Depends(get_session)):
    statement = select(Recurso).where(Recurso.id == recurso_id)
    result = await session.exec(statement)
    recurso = result.first()

    if not recurso:
        raise HTTPException(status_code=404, detail="Recurso não encontrado")

    await session.delete(recurso)
    await session.commit()
