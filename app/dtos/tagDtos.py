from pydantic import BaseModel

class TagCreate(BaseModel):
    nome: str

class TagRead(BaseModel):
    id: int
    nome: str