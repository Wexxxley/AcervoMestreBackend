from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.user import User
from app.models.tag import Tag
from app.dtos.tagDtos import TagCreate, TagRead

tag_router = APIRouter(prefix="/tags", tags=["Tags"])

@tag_router.get("/get_all", response_model=list[TagRead])
async def obter_todas_tags(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Retorna todas as tags cadastradas para uso em autocomplete.

    Retorna:
    - Lista de `TagRead` com todas as tags do sistema.

    Permissões:
    - Todos os usuários autenticados.
    """
    statement = select(Tag).order_by(Tag.nome)
    result = await session.exec(statement)
    return result.all()

@tag_router.post("/create", response_model=TagRead, status_code=201)
async def criar_tag(
    data: TagCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Cria uma nova tag no sistema.

    Parâmetros:
    - `data` (TagCreate): Nome da tag a ser criada.

    Retorna:
    - `TagRead` com os dados da tag criada.

    Erros possíveis:
    - 400: Caso a tag já exista.
    - 403: Caso o usuário não tenha permissão (apenas Gestor ou Coordenador).

    Permissões:
    - Gestor e Coordenador.
    """

    nova_tag = Tag(nome=data.nome.strip())
    session.add(nova_tag)

    try:
        await session.commit()
        await session.refresh(nova_tag)
        return nova_tag
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"A tag '{data.nome}' já existe."
        )


@tag_router.delete("/delete/{tag_id}", status_code=204)
async def deletar_tag(
    tag_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Remove uma tag do sistema.

    Parâmetros:
    - `tag_id` (int): ID da tag a ser removida.

    Retorna:
    - 204 No Content.

    Erros possíveis:
    - 403: Caso o usuário não seja Gestor.
    - 404: Caso a tag não seja encontrada.

    Permissões:
    - Apenas Gestor.
    """

    statement = select(Tag).where(Tag.id == tag_id)
    result = await session.exec(statement)
    tag = result.first()

    if not tag:
        raise HTTPException(status_code=404, detail="Tag não encontrada")

    await session.delete(tag)
    await session.commit()