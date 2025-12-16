from typing import Optional
from datetime import date, datetime, timezone
from sqlmodel import SQLModel, Field
from app.enums.perfil import Perfil 
from app.enums.status import Status 
from sqlalchemy import DateTime

class User(SQLModel, table=True):
    __tablename__ = "User"

    id: int | None = Field(default=None, primary_key=True)
    nome: str = Field(max_length=255)
    email: str = Field(max_length=255, unique=True, index=True)
    senha_hash: str | None = Field(default=None, nullable=True)

    perfil: Perfil 
    status: Status = Field(default=Status.Ativo)

    data_nascimento: date | None = None
    path_img: str | None = Field(default=None, max_length=255)
    
    criado_em: datetime = Field(
            default_factory=lambda: datetime.now(timezone.utc),
            sa_type=DateTime(timezone=True) 
        )