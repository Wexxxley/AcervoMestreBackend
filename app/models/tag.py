from typing import List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

from app.models.recurso_tag import RecursoTag

if TYPE_CHECKING:
    from app.models.recurso import Recurso

class Tag(SQLModel, table=True):
    __tablename__ = "Tag"

    id: int | None = Field(default=None, primary_key=True)
    nome: str = Field(max_length=100, unique=True, index=True)
    
    recursos: List["Recurso"] = Relationship(back_populates="tags", link_model=RecursoTag)