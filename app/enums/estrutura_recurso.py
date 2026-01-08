from enum import Enum

class EstruturaRecurso(str, Enum):
    """Enum para definir a estrutura/tipo de um recurso."""
    UPLOAD = "UPLOAD"
    URL = "URL"
    NOTA = "NOTA"
