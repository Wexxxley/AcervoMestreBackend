from enum import Enum

class Perfil(str, Enum):
    Gestor = "Gestor"
    Coordenador = "Coordenador"
    Professor = "Professor"
    Aluno = "Aluno"