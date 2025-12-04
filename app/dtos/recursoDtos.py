from sqlmodel import SQLModel
from datetime import datetime
from app.enums.visibilidade import Visibilidade
from app.enums.estrutura_recurso import EstruturaRecurso

class RecursoCreate(SQLModel):
    titulo: str
    descricao: str
    visibilidade: Visibilidade = Visibilidade.PUBLICO
    estrutura: EstruturaRecurso
    autor_id: int
    
    # Campos específicos opcionais
    conteudo_markdown: str | None = None
    storage_key: str | None = None
    mime_type: str | None = None
    tamanho_bytes: int | None = None
    url_externa: str | None = None

class RecursoUpdate(SQLModel):
    titulo: str | None = None
    descricao: str | None = None
    visibilidade: Visibilidade | None = None
    
    # Campos específicos opcionais
    conteudo_markdown: str | None = None
    storage_key: str | None = None
    mime_type: str | None = None
    tamanho_bytes: int | None = None
    url_externa: str | None = None

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
