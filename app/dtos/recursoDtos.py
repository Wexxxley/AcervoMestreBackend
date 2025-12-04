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
    """
    DTO de atualização para Recurso.

    Observação de design: o campo `estrutura` (tipo do recurso: UPLOAD/URL/NOTA)
    é intencionalmente imutável na aplicação — não é permitido alterar o tipo
    de um recurso após sua criação, pois isso implicaria em mudança de quais
    campos polimórficos são relevantes (por exemplo, transformar um UPLOAD em
    uma NOTA removeria os metadados do arquivo). Para alterar a estrutura do
    recurso seria necessária uma operação de criação de novo recurso e remoção
    do anterior.
    """

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
