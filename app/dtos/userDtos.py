from sqlmodel import SQLModel
from datetime import date
from app.enums.perfil import Perfil
from app.enums.status import Status

class UserCreate(SQLModel):
    nome: str
    email: str
    senha: str  # Recebe a senha pura, hash é gerado na lógica
    perfil: Perfil
    status: Status = Status.Ativo
    path_img: str | None = None
    data_nascimento: date | None = None

class UserUpdate(SQLModel):
    nome: str | None = None
    email: str | None = None
    perfil: Perfil | None = None
    status: Status | None = None
    path_img: str | None = None
    data_nascimento: date | None = None