from enum import Enum

class Status(str, Enum):
    Ativo = "Ativo"
    Inativo = "Inativo"
    AguardandoAtivacao = "AguardandoAtivacao"