from datetime import datetime, timezone
from sqlmodel import Relationship, SQLModel, Field
from sqlalchemy import DateTime, Text, ForeignKeyConstraint, Index, Column
from app.enums.visibilidade import Visibilidade
from app.enums.estrutura_recurso import EstruturaRecurso
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from app.models.tag import Tag
    from app.models.tag import RecursoTag
    
class Recurso(SQLModel, table=True):
    __tablename__ = "Recurso"

    id: int | None = Field(default=None, primary_key=True)
    titulo: str = Field(max_length=255)
    descricao: str = Field(max_length=1000)
    visibilidade: Visibilidade = Field(default=Visibilidade.PUBLICO)
    estrutura: EstruturaRecurso
    tags: List["Tag"] = Relationship(back_populates="recursos", link_model="RecursoTag")
    
    # Autor do recurso — referencia explícita com comportamento ondelete
    autor_id: int = Field(sa_column=Column(nullable=False))
    
    is_destaque: bool = Field(default=False)
    
    # Métricas (não-negativas)
    visualizacoes: int = Field(default=0, ge=0)
    downloads: int = Field(default=0, ge=0)
    curtidas: int = Field(default=0, ge=0)
    
    # Campos específicos por tipo (opcionais)
    # Para NOTA
    conteudo_markdown: str | None = Field(default=None, sa_column=Column(Text))
    
    # Para UPLOAD
    storage_key: str | None = Field(default=None, max_length=500)
    mime_type: str | None = Field(default=None, max_length=100)
    tamanho_bytes: int | None = Field(default=None, ge=0)
    
    # Para URL
    url_externa: str | None = Field(default=None, max_length=500)
    
    criado_em: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True)
    )

    # Foreign Key Constraint e Indexes para performance
    __table_args__ = (
        ForeignKeyConstraint(['autor_id'], ['User.id'], ondelete='RESTRICT', name='fk_recurso_autor_id'),
        Index('idx_recurso_estrutura', 'estrutura'),
        Index('idx_recurso_criado_em', 'criado_em'),
        Index('idx_recurso_autor_id', 'autor_id'),
        Index('idx_recurso_visibilidade', 'visibilidade'),
    )