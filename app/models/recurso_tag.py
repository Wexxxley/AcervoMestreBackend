# Arquivo: app/models/recurso_tag.py
from sqlmodel import SQLModel, Field

class RecursoTag(SQLModel, table=True):
    __tablename__ = "Recurso_Tag"

    recurso_id: int = Field(foreign_key="Recurso.id", primary_key=True, ondelete="CASCADE")
    tag_id: int = Field(foreign_key="Tag.id", primary_key=True, ondelete="CASCADE")