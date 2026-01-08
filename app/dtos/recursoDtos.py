from sqlmodel import SQLModel
from datetime import datetime
from pydantic import Field, model_validator, ConfigDict
from urllib.parse import urlparse
from app.dtos.tagDtos import TagRead
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

    @model_validator(mode='before')
    def validate_required_fields_for_estrutura(cls, values):  # type: ignore
        estrutura = values.get("estrutura")

        nota_fields = {"conteudo_markdown"}
        upload_fields = {"storage_key", "mime_type", "tamanho_bytes"}
        url_fields = {"url_externa"}

        if estrutura == EstruturaRecurso.NOTA:
            if not values.get("conteudo_markdown"):
                raise ValueError("campo 'conteudo_markdown' é obrigatório para estrutura NOTA")

            for field in upload_fields | url_fields:
                if values.get(field) is not None:
                    raise ValueError(f"campo '{field}' não deve ser fornecido para estrutura NOTA")

        elif estrutura == EstruturaRecurso.UPLOAD:
            if not values.get("storage_key") or not values.get("mime_type") or values.get("tamanho_bytes") is None:
                raise ValueError("campos 'storage_key', 'mime_type' e 'tamanho_bytes' são obrigatórios para estrutura UPLOAD")

            for field in nota_fields | url_fields:
                if values.get(field) is not None:
                    raise ValueError(f"campo '{field}' não deve ser fornecido para estrutura UPLOAD")

        elif estrutura == EstruturaRecurso.URL:
            if not values.get("url_externa"):
                raise ValueError("campo 'url_externa' é obrigatório para estrutura URL")

            for field in nota_fields | upload_fields:
                if values.get(field) is not None:
                    raise ValueError(f"campo '{field}' não deve ser fornecido para estrutura URL")

        return values

    @model_validator(mode='before')
    def validate_url_format(cls, values):  # type: ignore
        """Valida formato da URL quando fornecida."""
        url_externa = values.get("url_externa")
        if url_externa:
            try:
                parsed = urlparse(url_externa)
                if not parsed.scheme or not parsed.netloc:
                    raise ValueError("url_externa deve ser uma URL válida com esquema (http/https) e domínio")
                if parsed.scheme not in ['http', 'https']:
                    raise ValueError("url_externa deve usar esquema http ou https")
            except Exception:
                raise ValueError("url_externa deve ser uma URL válida")
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
    url_externa: str | None = None
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

    @model_validator(mode='before')
    def validate_polymorphic_fields(cls, values):  # type: ignore
        """
        Valida que apenas campos relevantes para o tipo de estrutura sejam fornecidos.
        Como estrutura não pode ser alterada no update, validamos apenas se campos
        incompatíveis não estão sendo definidos juntos.
        """
        # Campos específicos por estrutura
        nota_fields = {"conteudo_markdown"}
        upload_fields = {"storage_key", "mime_type", "tamanho_bytes"}
        url_fields = {"url_externa"}
        
        # Verificar se há mistura inválida de campos de diferentes estruturas
        provided_fields = {k for k, v in values.items() if v is not None and k in (nota_fields | upload_fields | url_fields)}
        
        if not provided_fields:
            return values  # Nenhum campo específico sendo atualizado
        
        # Determinar qual tipo de estrutura está sendo atualizado baseado nos campos fornecidos
        if provided_fields & nota_fields and provided_fields & (upload_fields | url_fields):
            raise ValueError("não é possível misturar campos de NOTA com campos de UPLOAD/URL no mesmo update")
        
        if provided_fields & upload_fields and provided_fields & (nota_fields | url_fields):
            raise ValueError("não é possível misturar campos de UPLOAD com campos de NOTA/URL no mesmo update")
        
        if provided_fields & url_fields and provided_fields & (nota_fields | upload_fields):
            raise ValueError("não é possível misturar campos de URL com campos de NOTA/UPLOAD no mesmo update")
        
        return values

    @model_validator(mode='before')
    def validate_url_format_update(cls, values):  # type: ignore
        """Valida formato da URL quando fornecida em updates."""
        url_externa = values.get("url_externa")
        if url_externa:
            try:
                parsed = urlparse(url_externa)
                if not parsed.scheme or not parsed.netloc:
                    raise ValueError("url_externa deve ser uma URL válida com esquema (http/https) e domínio")
                if parsed.scheme not in ['http', 'https']:
                    raise ValueError("url_externa deve usar esquema http ou https")
            except Exception:
                raise ValueError("url_externa deve ser uma URL válida")
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
    tags: list[TagRead] = []
    
    # Campos específicos
    conteudo_markdown: str | None = None
    storage_key: str | None = None
    mime_type: str | None = None
    tamanho_bytes: int | None = None    
    link_acesso: str | None = None
    
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


class RecursoDownloadResponse(SQLModel):
    """Resposta para operação de download de recurso."""
    message: str
    download_url: str | None = None
    downloads: int
