from typing import TYPE_CHECKING
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import DateTime, ForeignKeyConstraint, Index, Column

if TYPE_CHECKING:
    from app.models.playlist_recurso import PlaylistRecurso


class Playlist(SQLModel, table=True):
    __tablename__ = "Playlist"

    id: int | None = Field(default=None, primary_key=True)
    titulo: str = Field(max_length=255)
    descricao: str | None = Field(default=None, max_length=1000)
    
    # Autor da playlist — referencia explícita com comportamento ondelete
    autor_id: int = Field(sa_column=Column(nullable=False))
    
    criado_em: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True)
    )

    # Relacionamento N:N com Recurso através de PlaylistRecurso
    recursos: list["PlaylistRecurso"] = Relationship(back_populates="playlist")

    # Foreign Key Constraint e Indexes para performance
    __table_args__ = (
        ForeignKeyConstraint(['autor_id'], ['User.id'], ondelete='RESTRICT', name='fk_playlist_autor_id'),
        Index('idx_playlist_autor_id', 'autor_id'),
        Index('idx_playlist_criado_em', 'criado_em'),
    )
