from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.dtos.userDtos import UserCreate, UserRead, UserUpdate
from app.enums.status import Status
from app.models.user import User  
from app.core.database import get_session 
from app.core.security import get_password_hash
from sqlalchemy.exc import IntegrityError 
from fastapi import Query
from app.utils.pagination import PaginationParams
from app.utils.pagination import PaginatedResponse

user_router = APIRouter(prefix="/users", tags=["Users"])

@user_router.get("/get/{user_id}", response_model=UserRead)
async def get_user_by_id(user_id: int, session: AsyncSession = Depends(get_session)):
    statement = select(User).where(User.id == user_id)
    result = await session.exec(statement)
    user = result.first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user


@user_router.get("/get_all", response_model=PaginatedResponse[UserRead])
async def get_all_users(
    session: AsyncSession = Depends(get_session),
    pagination: PaginationParams = Depends(), 
    somente_ativos: bool = Query(True, description="Filtra apenas usuários ativos"),
):
    # Montar a query base (sem paginação)
    statement = select(User)
    if somente_ativos:
        statement = statement.where(User.status == Status.Ativo)

    # Contar o total de registros (Query separada)
    count_statement = select(func.count()).select_from(User)
    if somente_ativos:
        count_statement = count_statement.where(User.status == Status.Ativo)
        
    total_result = await session.exec(count_statement)
    total_items = total_result.one()

    # Aplicar a paginação na query principal
    offset = (pagination.page - 1) * pagination.per_page
    
    statement = statement.offset(offset).limit(pagination.per_page).order_by(User.id)
    
    result = await session.exec(statement)
    users = result.all()

    # Calcular total de páginas (para passar pro response)
    total_pages = (total_items + pagination.per_page - 1) // pagination.per_page

    # Retornar a estrutura PaginatedResponse
    return PaginatedResponse(
        items=users,
        total=total_items,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=total_pages
    )

@user_router.post("/create", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserCreate, session: AsyncSession = Depends(get_session)):
    
    user_dict = user_in.model_dump()
    senha_plana = user_dict.pop("senha")
    user_dict["senha_hash"] = get_password_hash(senha_plana)
    db_user = User.model_validate(user_dict)
    
    session.add(db_user)
    
    try:
        await session.commit()
        await session.refresh(db_user)
    except IntegrityError:
        await session.rollback() 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Já existe um usuário cadastrado com este email."
        )
        
    return db_user

@user_router.patch("/patch/{user_id}", response_model=UserRead)
async def update_user(user_id: int, user_input: UserUpdate, session: AsyncSession = Depends(get_session)):
    statement = select(User).where(User.id == user_id)
    result = await session.exec(statement)
    db_user = result.first()

    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user_data = user_input.model_dump(exclude_unset=True)

    for key, value in user_data.items():
        setattr(db_user, key, value)

    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user

@user_router.delete("/delete/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, session: AsyncSession = Depends(get_session)):
    statement = select(User).where(User.id == user_id)
    
    result = await session.exec(statement)
    user = result.first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

  
    user.status = Status.Inativo
    
    session.add(user) 
    await session.commit()