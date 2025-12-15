from sqlmodel import SQLModel
from datetime import datetime
from typing import Optional
from app.dtos.recursoDtos import RecursoRead


class PlaylistRecursoRead(SQLModel):
    """DTO para representar um recurso dentro de uma playlist (com ordem)."""
    recurso_id: int
    ordem: int
    recurso: RecursoRead


class PlaylistCreate(SQLModel):
    """DTO para criar uma nova playlist."""
    titulo: str
    descricao: str | None = None


class PlaylistUpdate(SQLModel):
    """DTO para atualizar uma playlist."""
    titulo: str | None = None
    descricao: str | None = None


class PlaylistRead(SQLModel):
    """DTO para retornar os detalhes de uma playlist com seus recursos."""
    id: int
    titulo: str
    descricao: str | None = None
    autor_id: int
    criado_em: datetime
    recursos: list[PlaylistRecursoRead] = []

    class Config:
        from_attributes = True


class PlaylistListRead(SQLModel):
    """DTO simplificado para listar playlists sem detalhe dos recursos."""
    id: int
    titulo: str
    descricao: str | None = None
    autor_id: int
    criado_em: datetime
    quantidade_recursos: int = 0

    class Config:
        from_attributes = True


class PlaylistAddRecursoRequest(SQLModel):
    """DTO para adicionar um recurso à playlist."""
    recurso_id: int


class PlaylistReordenacaoRequest(SQLModel):
    """DTO para reordenar recursos na playlist."""
    recursos_ordem: list[int]  # Lista de IDs de recursos na nova ordem
