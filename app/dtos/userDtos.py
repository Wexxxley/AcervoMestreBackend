from pydantic import EmailStr
from sqlmodel import SQLModel
from datetime import date
from pydantic import ConfigDict
from app.enums.perfil import Perfil
from app.enums.status import Status

class UserCreate(SQLModel):
    nome: str
    email: EmailStr
    perfil: Perfil
    senha: str | None = None  # Opcional (para fluxo de convite)    
    path_img: str | None = None 
    data_nascimento: date | None = None

class UserUpdate(SQLModel):
    nome: str | None = None
    email: EmailStr | None = None
    perfil: Perfil | None = None
    status: Status | None = None
    path_img: str | None = None
    data_nascimento: date | None = None

class UserRead(SQLModel):
    id: int | None = None
    nome: str
    email: EmailStr
    perfil: Perfil
    status: Status
    path_img: str | None = None
    data_nascimento: date | None = None

    model_config = ConfigDict(from_attributes=True)