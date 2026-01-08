from typing import TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import ForeignKeyConstraint, Index, UniqueConstraint

if TYPE_CHECKING:
    from app.models.playlist import Playlist
    from app.models.recurso import Recurso


class PlaylistRecurso(SQLModel, table=True):
    """
    Tabela associativa para relacionamento N:N entre Playlist e Recurso.
    Armazena a ordem dos recursos dentro da playlist.
    """
    __tablename__ = "PlaylistRecurso"

    playlist_id: int = Field(primary_key=True)
    recurso_id: int = Field(primary_key=True)
    
    # Campo ordem para permitir reordenação (arrastar e soltar)
    ordem: int = Field(ge=0)

    # Relacionamentos
    playlist: "Playlist" = Relationship(back_populates="recursos")
    recurso: "Recurso" = Relationship()

    # Foreign Key Constraints e Indexes
    __table_args__ = (
        ForeignKeyConstraint(['playlist_id'], ['Playlist.id'], ondelete='CASCADE', name='fk_playlist_recurso_playlist_id'),
        ForeignKeyConstraint(['recurso_id'], ['Recurso.id'], ondelete='CASCADE', name='fk_playlist_recurso_recurso_id'),
        Index('idx_playlist_recurso_playlist_id', 'playlist_id'),
        Index('idx_playlist_recurso_recurso_id', 'recurso_id'),
        Index('idx_playlist_recurso_ordem', 'playlist_id', 'ordem'),
        UniqueConstraint('playlist_id', 'ordem', name='uq_playlist_ordem_per_playlist'),
    )
