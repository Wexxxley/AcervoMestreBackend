from ast import List
from typing import TYPE_CHECKING
from sqlmodel import Relationship, SQLModel, Field

if TYPE_CHECKING:
    from app.models.recurso import Recurso

# Modelo da Tag
class Tag(SQLModel, table=True):
    __tablename__ = "Tag"

    id: int | None = Field(default=None, primary_key=True)
    nome: str = Field(max_length=100, unique=True, index=True)
    
    recursos: List["Recurso"] = Relationship(back_populates="tags", link_model="RecursoTag")

# Tabela associativa
class RecursoTag(SQLModel, table=True):
    __tablename__ = "Recurso_Tag"

    recurso_id: int = Field(foreign_key="Recurso.id", primary_key=True, ondelete="CASCADE")
    tag_id: int = Field(foreign_key="Tag.id", primary_key=True, ondelete="CASCADE")