from sqlmodel import SQLModel
from datetime import datetime
from pydantic import Field, HttpUrl, root_validator
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
    url_externa: HttpUrl | None = None

    @root_validator
    def validate_required_fields_for_estrutura(cls, values):
        estrutura = values.get("estrutura")
        if estrutura == EstruturaRecurso.NOTA:
            if not values.get("conteudo_markdown"):
                raise ValueError("campo 'conteudo_markdown' é obrigatório para estrutura NOTA")
        elif estrutura == EstruturaRecurso.UPLOAD:
            if not values.get("storage_key") or not values.get("mime_type") or values.get("tamanho_bytes") is None:
                raise ValueError("campos 'storage_key', 'mime_type' e 'tamanho_bytes' são obrigatórios para estrutura UPLOAD")
        elif estrutura == EstruturaRecurso.URL:
            if not values.get("url_externa"):
                raise ValueError("campo 'url_externa' é obrigatório para estrutura URL")
        return values

class RecursoUpdate(SQLModel):
    titulo: str | None = Field(None, max_length=255)
    descricao: str | None = Field(None, max_length=1000)
    visibilidade: Visibilidade | None = None
    
    # Campos específicos opcionais
    conteudo_markdown: str | None = Field(None, max_length=5000)
    storage_key: str | None = Field(None, max_length=500)
    mime_type: str | None = Field(None, max_length=100)
    tamanho_bytes: int | None = None
    url_externa: HttpUrl | None = None

    @root_validator
    def validate_update_fields_for_estrutura(cls, values):
        # No update, só validar requisitos quando a estrutura é fornecida na requisição
        estrutura = values.get("estrutura")
        if estrutura == EstruturaRecurso.NOTA:
            if values.get("conteudo_markdown") is None:
                raise ValueError("ao alterar estrutura para NOTA, 'conteudo_markdown' é obrigatório")
        elif estrutura == EstruturaRecurso.UPLOAD:
            # exigir todos os campos de upload quando estrutura for alterada para UPLOAD
            if values.get("storage_key") is None or values.get("mime_type") is None or values.get("tamanho_bytes") is None:
                raise ValueError("ao alterar estrutura para UPLOAD, 'storage_key', 'mime_type' e 'tamanho_bytes' são obrigatórios")
        elif estrutura == EstruturaRecurso.URL:
            if values.get("url_externa") is None:
                raise ValueError("ao alterar estrutura para URL, 'url_externa' é obrigatório")
        return values

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
    url_externa: HttpUrl | None = None
    
    criado_em: datetime

    class Config:
        from_attributes = True
