from sqlmodel import SQLModel
from datetime import date
from app.enums.perfil import Perfil
from app.enums.status import Status

class UserCreate(SQLModel):
    nome: str
    email: str
    perfil: Perfil
    senha: str | None = None  # Opcional (para fluxo de convite)    
    path_img: str | None = None 
    data_nascimento: date | None = None

class UserUpdate(SQLModel):
    nome: str | None = None
    email: str | None = None
    perfil: Perfil | None = None
    status: Status | None = None
    path_img: str | None = None
    data_nascimento: date | None = None

class UserRead(SQLModel):
    id: int | None = None
    nome: str
    email: str
    perfil: Perfil
    status: Status
    path_img: str | None = None
    data_nascimento: date | None = None

    class Config:
        from_attributes = True