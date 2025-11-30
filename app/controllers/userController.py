from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.dtos.userDtos import UserCreate, UserUpdate
from app.models.user import User  
from app.core.database import get_session 
from app.core.security import get_password_hash
from sqlalchemy.exc import IntegrityError 

user_router = APIRouter(prefix="/users", tags=["Users"])

@user_router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
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

@user_router.get("/", response_model=List[User])
async def get_all_users(session: AsyncSession = Depends(get_session)):
    statement = select(User)
    result = await session.exec(statement)
    return result.all() 

@user_router.get("/{user_id}", response_model=User)
async def get_user_by_id(user_id: int, session: AsyncSession = Depends(get_session)):
    statement = select(User).where(User.id == user_id)
    result = await session.exec(statement)
    user = result.first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user

@user_router.patch("/{user_id}", response_model=User)
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

@user_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, session: AsyncSession = Depends(get_session)):
    statement = select(User).where(User.id == user_id)
    
    result = await session.exec(statement)
    user = result.first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    await session.delete(user)
    await session.commit()