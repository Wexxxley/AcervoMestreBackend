from enum import Enum

class Visibilidade(str, Enum):
    """Enum para definir a visibilidade de um recurso."""
    PUBLICO = "PUBLICO"
    PRIVADO = "PRIVADO"
