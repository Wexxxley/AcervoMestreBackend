from sqlmodel import SQLModel
from datetime import datetime
from pydantic import Field
from app.enums.visibilidade import Visibilidade
from app.enums.estrutura_recurso import EstruturaRecurso

class RecursoCreate(SQLModel):
    titulo: str = Field(..., max_length=255)
    descricao: str = Field(..., max_length=1000)
    visibilidade: Visibilidade = Visibilidade.PUBLICO
    estrutura: EstruturaRecurso
    autor_id: int
    
    # Campos específicos opcionais
    conteudo_markdown: str | None = Field(None, max_length=5000)
    storage_key: str | None = Field(None, max_length=500)
    mime_type: str | None = Field(None, max_length=100)
    tamanho_bytes: int | None = None
    url_externa: str | None = None

class RecursoUpdate(SQLModel):
    titulo: str | None = Field(None, max_length=255)
    descricao: str | None = Field(None, max_length=1000)
    visibilidade: Visibilidade | None = None
    
    # Campos específicos opcionais
    conteudo_markdown: str | None = Field(None, max_length=5000)
    storage_key: str | None = Field(None, max_length=500)
    mime_type: str | None = Field(None, max_length=100)
    tamanho_bytes: int | None = None
    url_externa: str | None = Field(None, max_length=500)

class RecursoRead(SQLModel):
    id: int
    titulo: str
    descricao: str
    visibilidade: Visibilidade
    estrutura: EstruturaRecurso
    autor_id: int
    is_destaque: bool
    visualizacoes: int
    downloads: int
    curtidas: int
    
    # Campos específicos
    conteudo_markdown: str | None = None
    storage_key: str | None = None
    mime_type: str | None = None
    tamanho_bytes: int | None = None
    url_externa: str | None = None
    
    criado_em: datetime

    class Config:
        from_attributes = True
