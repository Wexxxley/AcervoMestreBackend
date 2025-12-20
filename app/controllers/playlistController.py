from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Optional

from app.dtos.playlistDtos import (
    PlaylistCreate,
    PlaylistUpdate,
    PlaylistRead,
    PlaylistListRead,
    PlaylistAddRecursoRequest,
    PlaylistReordenacaoRequest,
)
from app.models.playlist import Playlist
from app.models.playlist_recurso import PlaylistRecurso
from app.models.recurso import Recurso
from app.models.user import User
from app.core.database import get_session
from app.core.security import get_current_user
from app.utils.pagination import PaginationParams, PaginatedResponse

playlist_router = APIRouter(prefix="/playlists", tags=["Playlists"])


# ============================================================================
# Validações e funções auxiliares
# ============================================================================

async def verificar_playlist_existe(
    playlist_id: int,
    session: AsyncSession
) -> Playlist:
    """Verifica se playlist existe, lança 404 caso contrário."""
    statement = select(Playlist).where(Playlist.id == playlist_id)
    result = await session.exec(statement)
    playlist = result.first()
    
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist não encontrada")
    
    return playlist


async def verificar_autoria(
    playlist: Playlist,
    current_user: User | None
) -> None:
    """Verifica se o usuário é o autor da playlist, lança 403 caso contrário."""
    if not current_user or current_user.id != playlist.autor_id:
        raise HTTPException(
            status_code=403,
            detail="Permissão negada. Apenas o autor pode realizar esta ação."
        )


async def verificar_recurso_existe(
    recurso_id: int,
    session: AsyncSession
) -> Recurso:
    """Verifica se recurso existe, lança 404 caso contrário."""
    statement = select(Recurso).where(Recurso.id == recurso_id)
    result = await session.exec(statement)
    recurso = result.first()
    
    if not recurso:
        raise HTTPException(status_code=404, detail="Recurso não encontrado")
    
    return recurso


# ============================================================================
# Endpoints: CRUD Padrão
# ============================================================================

@playlist_router.post("/", response_model=PlaylistRead, status_code=201)
async def criar_playlist(
    data: PlaylistCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    [RF12] Criar Playlist
    
    Cria uma nova playlist vazia associada ao usuário autenticado.
    Requer autenticação.
    """
    # Validação de título é feita pelo DTO (`PlaylistCreate`) via Pydantic
    
    nova_playlist = Playlist(
        titulo=data.titulo.strip(),
        descricao=data.descricao.strip() if data.descricao and data.descricao.strip() else None,
        autor_id=current_user.id,
    )
    
    session.add(nova_playlist)
    await session.commit()
    
    # Eagerly load recursos relationship before returning
    result = await session.exec(
        select(Playlist)
        .options(selectinload(Playlist.recursos))
        .where(Playlist.id == nova_playlist.id)
    )
    playlist_with_recursos = result.one()
    return playlist_with_recursos


@playlist_router.get("/{playlist_id}", response_model=PlaylistRead)
async def obter_playlist_por_id(
    playlist_id: int,
    session: AsyncSession = Depends(get_session),
):
    """
    Obter detalhes de uma playlist por ID.
    Retorna a playlist com a lista de recursos ordenados.
    """
    # Eager load playlist com recursos e seus objetos Recurso aninhados
    statement = (
        select(Playlist)
        .where(Playlist.id == playlist_id)
        .options(
            selectinload(Playlist.recursos).selectinload(PlaylistRecurso.recurso)
        )
    )
    result = await session.exec(statement)
    playlist = result.first()
    
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist não encontrada")
    
    return playlist


@playlist_router.get("", response_model=PaginatedResponse[PlaylistListRead])
async def listar_playlists(
    session: AsyncSession = Depends(get_session),
    pagination: PaginationParams = Depends(),
    autor_id: Optional[int] = Query(None, description="Filtrar por autor_id"),
):
    """
    Listar playlists (com opção de filtro por autor).
    Retorna lista simplificada sem detalhe dos recursos.
    """
    # Usar eager loading para evitar N+1 ao carregar os recursos das playlists
    statement = select(Playlist).options(selectinload(Playlist.recursos))
    
    if autor_id:
        statement = statement.where(Playlist.autor_id == autor_id)
    
    # Contar total de registros
    count_statement = select(func.count()).select_from(Playlist)
    if autor_id:
        count_statement = count_statement.where(Playlist.autor_id == autor_id)
    
    total_result = await session.exec(count_statement)
    total_items = total_result.one()
    
    # Aplicar paginação
    offset = (pagination.page - 1) * pagination.per_page
    statement = statement.offset(offset).limit(pagination.per_page).order_by(Playlist.id.desc())
    
    result = await session.exec(statement)
    playlists = result.all()
    
    # Enriquecer com quantidade de recursos
    playlists_com_quantidade = []
    for playlist in playlists:
        # `recursos` já foi carregado por selectinload; evita N+1 queries
        quantidade = len(playlist.recursos) if playlist.recursos else 0
        
        playlist_list = PlaylistListRead(
            id=playlist.id,
            titulo=playlist.titulo,
            descricao=playlist.descricao,
            autor_id=playlist.autor_id,
            criado_em=playlist.criado_em,
            quantidade_recursos=quantidade,
        )
        playlists_com_quantidade.append(playlist_list)
    
    return PaginatedResponse(
        items=playlists_com_quantidade,
        page=pagination.page,
        per_page=pagination.per_page,
        total=total_items,
    )


@playlist_router.put("/{playlist_id}", response_model=PlaylistRead)
async def editar_playlist(
    playlist_id: int,
    data: PlaylistUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Editar uma playlist (título e descrição).
    Apenas o autor pode editar.
    """
    playlist = await verificar_playlist_existe(playlist_id, session)
    await verificar_autoria(playlist, current_user)
    # Validar que ao menos um campo foi enviado para atualização
    if data.titulo is None and data.descricao is None:
        raise HTTPException(
            status_code=400,
            detail="Pelo menos um campo (titulo ou descricao) deve ser informado para atualização"
        )
    
    if data.titulo is not None:
        playlist.titulo = data.titulo.strip()
    
    if data.descricao is not None:
        playlist.descricao = data.descricao.strip() if data.descricao.strip() else None
    
    session.add(playlist)
    await session.commit()
    
    # Eagerly load recursos relationship before returning
    result = await session.exec(
        select(Playlist)
        .options(selectinload(Playlist.recursos))
        .where(Playlist.id == playlist.id)
    )
    playlist_with_recursos = result.one()
    return playlist_with_recursos


@playlist_router.delete("/{playlist_id}", status_code=204)
async def deletar_playlist(
    playlist_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Deletar uma playlist.
    Apenas o autor pode deletar.
    Nota: A tabela associativa será deletada em cascata, mas os recursos serão mantidos.
    """
    playlist = await verificar_playlist_existe(playlist_id, session)
    await verificar_autoria(playlist, current_user)
    
    await session.delete(playlist)
    await session.commit()


# ============================================================================
# Endpoints: Gerenciar Recursos na Playlist [RF13]
# ============================================================================

@playlist_router.post("/{playlist_id}/recursos", status_code=201)
async def adicionar_recurso_playlist(
    playlist_id: int,
    data: PlaylistAddRecursoRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Adicionar um recurso existente à playlist.
    Apenas o autor da playlist pode adicionar.
    """
    playlist = await verificar_playlist_existe(playlist_id, session)
    await verificar_autoria(playlist, current_user)
    
    # Verificar se recurso existe
    recurso = await verificar_recurso_existe(data.recurso_id, session)
    
    # Verificar se recurso já está na playlist
    statement = select(PlaylistRecurso).where(
        (PlaylistRecurso.playlist_id == playlist_id) &
        (PlaylistRecurso.recurso_id == data.recurso_id)
    )
    result = await session.exec(statement)
    if result.first():
        raise HTTPException(
            status_code=409,
            detail="Recurso já está presente nesta playlist"
        )
    
    # Obter a próxima ordem (última ordem + 1)
    statement_ordem = select(func.max(PlaylistRecurso.ordem)).where(
        PlaylistRecurso.playlist_id == playlist_id
    )
    resultado_ordem = await session.exec(statement_ordem)
    proxima_ordem = (resultado_ordem.one() or -1) + 1

    # Criar associação
    playlist_recurso = PlaylistRecurso(
        playlist_id=playlist_id,
        recurso_id=data.recurso_id,
        ordem=proxima_ordem,
    )

    session.add(playlist_recurso)

    try:
        await session.commit()
    except IntegrityError:
        # Possível colisão de ordem em alta concorrência; refaz cálculo e tenta novamente
        await session.rollback()
        resultado_ordem = await session.exec(statement_ordem)
        proxima_ordem = (resultado_ordem.one() or -1) + 1
        # Recriar o objeto após rollback para evitar problemas de estado no session
        novo_playlist_recurso = PlaylistRecurso(
            playlist_id=playlist_id,
            recurso_id=data.recurso_id,
            ordem=proxima_ordem,
        )
        session.add(novo_playlist_recurso)
        await session.commit()
    
    return {"message": "Recurso adicionado à playlist com sucesso", "ordem": proxima_ordem}


@playlist_router.delete("/{playlist_id}/recursos/{recurso_id}", status_code=204)
async def remover_recurso_playlist(
    playlist_id: int,
    recurso_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Remover um recurso da playlist.
    Apenas o autor da playlist pode remover.
    Nota: O recurso não é deletado, apenas desassociado.
    """
    playlist = await verificar_playlist_existe(playlist_id, session)
    await verificar_autoria(playlist, current_user)
    
    # Verificar se o recurso está na playlist
    statement = select(PlaylistRecurso).where(
        (PlaylistRecurso.playlist_id == playlist_id) &
        (PlaylistRecurso.recurso_id == recurso_id)
    )
    result = await session.exec(statement)
    playlist_recurso = result.first()
    
    if not playlist_recurso:
        raise HTTPException(
            status_code=404,
            detail="Recurso não encontrado nesta playlist"
        )
    
    # Deletar associação
    await session.delete(playlist_recurso)
    
    # Reordenar os recursos restantes para não haver lacunas
    statement_reordenar = select(PlaylistRecurso).where(
        PlaylistRecurso.playlist_id == playlist_id
    ).order_by(PlaylistRecurso.ordem)
    
    resultado_reordenar = await session.exec(statement_reordenar)
    recursos_restantes = resultado_reordenar.all()
    
    for idx, pr in enumerate(recursos_restantes):
        pr.ordem = idx
        session.add(pr)
    
    await session.commit()


@playlist_router.put("/{playlist_id}/reordenar", status_code=200)
async def reordenar_recursos_playlist(
    playlist_id: int,
    data: PlaylistReordenacaoRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Reordenar recursos na playlist.
    Recebe uma lista de IDs de recursos na nova ordem.
    Apenas o autor da playlist pode reordenar.
    """
    playlist = await verificar_playlist_existe(playlist_id, session)
    await verificar_autoria(playlist, current_user)
    
    if not data.recurso_ids_ordem:
        raise HTTPException(status_code=400, detail="Lista de recursos vazia")
    
    # Verificar se há IDs duplicados na lista de reordenação
    if len(set(data.recurso_ids_ordem)) != len(data.recurso_ids_ordem):
        raise HTTPException(
            status_code=400,
            detail="A lista de recursos contém IDs duplicados"
        )
    # Verificar se todos os IDs existem na playlist
    statement = select(PlaylistRecurso).where(
        PlaylistRecurso.playlist_id == playlist_id
    )
    result = await session.exec(statement)
    recursos_playlist = result.all()
    
    ids_na_playlist = {pr.recurso_id for pr in recursos_playlist}
    
    for recurso_id in data.recurso_ids_ordem:
        if recurso_id not in ids_na_playlist:
            raise HTTPException(
                status_code=400,
                detail=f"Recurso {recurso_id} não está nesta playlist"
            )
    
    if len(data.recurso_ids_ordem) != len(ids_na_playlist):
        raise HTTPException(
            status_code=400,
            detail="A lista deve conter todos os recursos da playlist"
        )
    
    # Para evitar conflito com a constraint UNIQUE (playlist_id, ordem),
    # deletamos todos os registros e inserimos novamente com as novas ordens
    for pr in recursos_playlist:
        await session.delete(pr)
    
    await session.flush()  # Garante que os deletes sejam executados antes dos inserts
    
    # Inserir novamente com as novas ordens
    for nova_ordem, recurso_id in enumerate(data.recurso_ids_ordem):
        novo_pr = PlaylistRecurso(
            playlist_id=playlist_id,
            recurso_id=recurso_id,
            ordem=nova_ordem
        )
        session.add(novo_pr)
    
    await session.commit()
    
    return {"message": "Recursos reordenados com sucesso"}
