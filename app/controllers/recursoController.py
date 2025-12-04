from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import func, or_, update
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.dtos.recursoDtos import RecursoCreate, RecursoRead, RecursoUpdate
from app.models.recurso import Recurso
from app.models.user import User
from app.core.database import get_session
from app.core.security import get_current_user
from app.enums.visibilidade import Visibilidade
from app.enums.perfil import Perfil
from app.utils.pagination import PaginationParams, PaginatedResponse

recurso_router = APIRouter(prefix="/recursos", tags=["Recursos"])

@recurso_router.get("/get/{recurso_id}", response_model=RecursoRead)
async def get_recurso_by_id(
    recurso_id: int, 
    session: AsyncSession = Depends(get_session),
    current_user: User | None = Depends(get_current_user)
):
    """Retorna um recurso por ID e incrementa o contador de visualizações.

    Parâmetros:
    - `recurso_id` (int): ID do recurso a ser retornado.
    - `session` (AsyncSession): sessão do banco (injeção de dependência).
    - `current_user` (User|None): usuário autenticado (se houver).

    Retorna:
    - `RecursoRead` com os dados do recurso solicitado.

    Erros possíveis:
    - 404: recurso não encontrado.
    - 403: acesso negado se recurso for PRIVADO e usuário for ALUNO ou não autenticado.
    - 401: quando autenticação for necessária para operações protegidas (usada em outras rotas).
    """
    statement = select(Recurso).where(Recurso.id == recurso_id)
    result = await session.exec(statement)
    recurso = result.first()

    if not recurso:
        raise HTTPException(status_code=404, detail="Recurso não encontrado")

    if recurso.visibilidade == Visibilidade.PRIVADO:
        # Recursos privados só podem ser vistos por usuários que NÃO são ALUNO
        if not current_user or current_user.perfil == Perfil.Aluno:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado a recurso privado",
            )

    await session.exec(
        update(Recurso)
        .where(Recurso.id == recurso_id)
        .values(visualizacoes=Recurso.visualizacoes + 1)
    )

    # Persistir a atualização e retornar o recurso atualizado
    await session.commit()

    statement = select(Recurso).where(Recurso.id == recurso_id)
    result = await session.exec(statement)
    recurso = result.first()

    return recurso


@recurso_router.get("/get_all", response_model=PaginatedResponse[RecursoRead])
async def get_all_recursos(
    session: AsyncSession = Depends(get_session),
    pagination: PaginationParams = Depends(),
    palavra_chave: str | None = Query(None, description="Busca por título ou descrição"),
    estrutura: str | None = Query(None, description="Filtra por estrutura (UPLOAD, URL, NOTA)"),
    current_user: User | None = Depends(get_current_user),
):
    """Lista recursos com paginação e filtros.

    Parâmetros:
    - `session` (AsyncSession): sessão do banco.
    - `pagination` (PaginationParams): parâmetros de paginação (`page`, `per_page`).
    - `palavra_chave` (str|None): busca em `titulo` e `descricao`.
    - `estrutura` (str|None): filtra por `UPLOAD`, `URL` ou `NOTA`.
    - `current_user` (User|None): usuário autenticado (se houver) para aplicar filtros de visibilidade.

    Retorna:
    - `PaginatedResponse[RecursoRead]` com itens paginados e metadados (total, páginas).

    Regras de visibilidade:
    - ALUNO e usuários não autenticados veem apenas recursos `PUBLICO`.
    - Outros perfis (Professor, Coordenador, Gestor) veem todos os recursos.
    """
    # Montar a query base
    statement = select(Recurso)
    
    # Aplicar filtros de visibilidade
    # Usuários ALUNO e não autenticados só veem recursos PUBLICOS
    # Usuários autenticados não-ALUNO (Professor, Coordenador, Gestor) veem TODOS os recursos
    if current_user is None or (current_user and current_user.perfil == Perfil.Aluno):
        # Alunos e usuários não autenticados só veem PUBLICOS
        statement = statement.where(Recurso.visibilidade == Visibilidade.PUBLICO)
    # Usuários autenticados não-ALUNO veem todos os recursos (sem filtro adicional)
    
    # Filtro por palavra-chave
    if palavra_chave:
        statement = statement.where(
            or_(
                Recurso.titulo.ilike(f"%{palavra_chave}%"),
                Recurso.descricao.ilike(f"%{palavra_chave}%")
            )
        )
    
    # Filtro por estrutura
    if estrutura:
        statement = statement.where(Recurso.estrutura == estrutura)

    # Contar o total de registros (com os mesmos filtros)
    count_statement = select(func.count()).select_from(Recurso)
    
    # Aplicar os mesmos filtros de visibilidade na contagem
    if current_user is None or (current_user and current_user.perfil == Perfil.Aluno):
        # Alunos e usuários não autenticados só contam PUBLICOS
        count_statement = count_statement.where(Recurso.visibilidade == Visibilidade.PUBLICO)
    # Usuários autenticados não-ALUNO contam todos os recursos (sem filtro adicional)
    
    if palavra_chave:
        count_statement = count_statement.where(
            or_(
                Recurso.titulo.ilike(f"%{palavra_chave}%"),
                Recurso.descricao.ilike(f"%{palavra_chave}%")
            )
        )
    
    if estrutura:
        count_statement = count_statement.where(Recurso.estrutura == estrutura)
        
    total_result = await session.exec(count_statement)
    total_items = total_result.one()

    # Aplicar a paginação
    offset = (pagination.page - 1) * pagination.per_page
    statement = statement.offset(offset).limit(pagination.per_page).order_by(Recurso.criado_em.desc())
    
    result = await session.exec(statement)
    recursos = result.all()

    # Calcular total de páginas
    total_pages = (total_items + pagination.per_page - 1) // pagination.per_page

    return PaginatedResponse(
        items=recursos,
        total=total_items,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=total_pages
    )


@recurso_router.post("/create", response_model=RecursoRead, status_code=status.HTTP_201_CREATED)
async def create_recurso(
    recurso_in: RecursoCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Cria um novo recurso.

    Parâmetros:
    - `recurso_in` (RecursoCreate): dados do recurso a criar.
    - `session` (AsyncSession): sessão do banco.
    - `current_user` (User): usuário autenticado; será usado como autor do recurso.

    Comportamento:
    - `autor_id` é derivado do `current_user` para evitar impersonation.

    Retorna:
    - `RecursoRead` com os dados do recurso criado (HTTP 201).

    Erros possíveis:
    - 401: quando não autenticado.
    - 404: autor não encontrado (sanity check; improvável se `current_user` válido).
    - 422: validação de campos específicos por `estrutura`.
    """
    # Requer autenticação
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Autenticação necessária")

    # Derivar autor_id do usuário autenticado para evitar impersonation
    recurso_dict = recurso_in.model_dump()
    recurso_dict["autor_id"] = current_user.id


    db_recurso = Recurso.model_validate(recurso_dict)

    session.add(db_recurso)
    await session.commit()
    await session.refresh(db_recurso)

    return db_recurso


@recurso_router.patch("/patch/{recurso_id}", response_model=RecursoRead)
async def update_recurso(
    recurso_id: int, 
    recurso_in: RecursoUpdate, 
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Atualiza campos de um recurso existente.

    Parâmetros:
    - `recurso_id` (int): ID do recurso a ser atualizado.
    - `recurso_in` (RecursoUpdate): campos a atualizar (parciais permitidas).
    - `session` (AsyncSession): sessão do banco.
    - `current_user` (User): usuário autenticado (autor ou Coordenador exigido para permissão).

    Regras de autorização:
    - Apenas o autor do recurso ou usuários com `Perfil.Coordenador` podem editar.

    Retorna:
    - `RecursoRead` com os dados atualizados.

    Erros possíveis:
    - 401: não autenticado.
    - 403: permissão negada para editar.
    - 404: recurso não encontrado.
    - 422: tentativa de atualizar campos polimórficos de maneira inconsistente.
    """

    statement = select(Recurso).where(Recurso.id == recurso_id)
    result = await session.exec(statement)
    db_recurso = result.first()

    if not db_recurso:
        raise HTTPException(status_code=404, detail="Recurso não encontrado")

    # Requer autenticação
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Autenticação necessária")

    # Permissão: apenas autor ou Coordenador podem editar
    if not (current_user.id == db_recurso.autor_id or current_user.perfil == Perfil.Coordenador):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão negada para editar recurso")

    recurso_data = recurso_in.model_dump(exclude_unset=True)

    # Validate that updated fields are compatible with the resource's estrutura type
    estrutura_allowed_fields = {
        "UPLOAD": {"titulo", "descricao", "visibilidade", "is_destaque", "storage_key", "mime_type", "tamanho_bytes"},
        "URL": {"titulo", "descricao", "visibilidade", "is_destaque", "url_externa"},
        "NOTA": {"titulo", "descricao", "visibilidade", "is_destaque", "conteudo_markdown"},
    }
    estrutura = db_recurso.estrutura
    allowed_fields = estrutura_allowed_fields.get(estrutura, set())
    for field in recurso_data:
        if field not in allowed_fields:
            raise HTTPException(
                status_code=422,
                detail=f"Campo '{field}' não é permitido para recursos do tipo '{estrutura}'"
            )

    for key, value in recurso_data.items():
        setattr(db_recurso, key, value)

    session.add(db_recurso)
    await session.commit()
    await session.refresh(db_recurso)
    return db_recurso


@recurso_router.delete("/delete/{recurso_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recurso(
    recurso_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Exclui um recurso existente.

    Parâmetros:
    - `recurso_id` (int): ID do recurso a ser excluído.
    - `session` (AsyncSession): sessão do banco.
    - `current_user` (User): usuário autenticado (autor ou Coordenador exigido para permissão).

    Regras de autorização:
    - Apenas o autor do recurso ou usuários com `Perfil.Coordenador` podem excluir.

    Retorno:
    - 204 No Content em sucesso.

    Erros possíveis:
    - 401: não autenticado.
    - 403: permissão negada para excluir.
    - 404: recurso não encontrado.
    """

    statement = select(Recurso).where(Recurso.id == recurso_id)
    result = await session.exec(statement)
    recurso = result.first()

    if not recurso:
        raise HTTPException(status_code=404, detail="Recurso não encontrado")

    # Requer autenticação
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Autenticação necessária")

    # Permissão: apenas autor ou Coordenador podem deletar
    if not (current_user.id == recurso.autor_id or current_user.perfil == Perfil.Coordenador):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão negada para excluir recurso")

    await session.delete(recurso)
    await session.commit()
