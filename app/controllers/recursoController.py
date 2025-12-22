from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy import func, or_, update
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Optional, List
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.dtos.recursoDtos import RecursoRead, RecursoUpdate
from app.dtos.tagDtos import TagRead
from app.models.recurso import Recurso
from app.models.recurso_tag import RecursoTag
from app.models.tag import Tag
from app.models.user import User
from app.core.database import get_session
from app.core.security import get_current_user, get_current_user_optional
from app.enums.visibilidade import Visibilidade
from app.enums.estrutura_recurso import EstruturaRecurso
from app.enums.perfil import Perfil
from app.utils.pagination import PaginationParams, PaginatedResponse
from app.services.s3_service import s3_service

recurso_router = APIRouter(prefix="/recursos", tags=["Recursos"])

# ============================================================================
# Função Auxiliar (Interna)
# ============================================================================
def preencher_link_acesso(recurso: Recurso) -> RecursoRead:
    """
    Converte o model de banco (Recurso) para o DTO (RecursoRead)
    e preenche o campo 'link_acesso' dinamicamente.
    """
    
    # Conversão manual de tags para evitar erro de validação do Pydantic
    tags_convertidas = []
    for tag in recurso.tags:
        try:
            tags_convertidas.append(TagRead.model_validate(tag, from_attributes=True))
        except:
            tags_convertidas.append(TagRead(**tag.model_dump()))

    # Cria o DTO. Note que removemos 'url_externa' do construtor.
    dto = RecursoRead(
        id=recurso.id,
        titulo=recurso.titulo,
        descricao=recurso.descricao,
        visibilidade=recurso.visibilidade,
        estrutura=recurso.estrutura,
        autor_id=recurso.autor_id,
        is_destaque=recurso.is_destaque,
        visualizacoes=recurso.visualizacoes,
        downloads=recurso.downloads,
        curtidas=recurso.curtidas,
        criado_em=recurso.criado_em,
        tags=tags_convertidas,
        
        # Campos opcionais restantes
        conteudo_markdown=recurso.conteudo_markdown,
        storage_key=recurso.storage_key,
        mime_type=recurso.mime_type,
        tamanho_bytes=recurso.tamanho_bytes,
        
        # link_acesso começa nulo e é preenchido abaixo
        link_acesso=None 
    )
    
    # Lógica de preenchimento do Link
    if recurso.estrutura == EstruturaRecurso.UPLOAD and recurso.storage_key:
        dto.link_acesso = s3_service.get_file_url(recurso.storage_key, download=False)
    
    elif recurso.estrutura == EstruturaRecurso.URL:
        # Pegamos do banco e jogamos no link_acesso
        dto.link_acesso = recurso.url_externa
        
    return dto

# ============================================================================
# Endpoints de Leitura
# ============================================================================

@recurso_router.get("/get/{recurso_id}", response_model=RecursoRead)
async def get_recurso_by_id(
    recurso_id: int, 
    session: AsyncSession = Depends(get_session),
    current_user: User | None = Depends(get_current_user_optional)
):
    """Retorna um recurso por ID e incrementa o contador de visualizações.
    
    O objeto retornado incluirá o campo `link_acesso` preenchido.

    Parâmetros:
    - `recurso_id` (int): ID do recurso a ser retornado.
    - `session` (AsyncSession): sessão do banco (injeção de dependência).
    - `current_user` (User|None): usuário autenticado (se houver).

    Retorna:
    - `RecursoRead` com os dados do recurso solicitado e suas tags.

    Erros possíveis:
    - 404: recurso não encontrado.
    - 403: acesso negado se recurso for PRIVADO e usuário for ALUNO ou não autenticado.
    
    Permissões:
    - Acesso público para recursos PÚBLICOS.
    - Autenticação necessária para recursos PRIVADOS (exceto Alunos).
    """
    # 1. Primeira busca (carregando tags)
    statement = (
        select(Recurso)
        .where(Recurso.id == recurso_id)
        .options(selectinload(Recurso.tags))
    )
    result = await session.exec(statement)
    recurso = result.first()

    if not recurso:
        raise HTTPException(status_code=404, detail="Recurso não encontrado")

    if recurso.visibilidade == Visibilidade.PRIVADO:
        if not current_user or current_user.perfil == Perfil.Aluno:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado a recurso privado",
            )

    # 2. Incrementa visualização
    await session.exec(
        update(Recurso)
        .where(Recurso.id == recurso_id)
        .values(visualizacoes=Recurso.visualizacoes + 1)
    )
    await session.commit()

    # 3. Segunda busca (CRUCIAL: Recarregar tags após commit)
    # Como houve commit, o objeto anterior pode estar expirado.
    # Buscamos novamente garantindo que as tags venham juntas para o retorno.
    statement = (
        select(Recurso)
        .where(Recurso.id == recurso_id)
        .options(selectinload(Recurso.tags))
    )
    result = await session.exec(statement)
    recurso_atualizado = result.first()

    # Retorna usando a função auxiliar que injeta o link
    return preencher_link_acesso(recurso_atualizado)

@recurso_router.get("/get_all", response_model=PaginatedResponse[RecursoRead])
async def get_all_recursos(
    session: AsyncSession = Depends(get_session),
    pagination: PaginationParams = Depends(),
    palavra_chave: str | None = Query(None, description="Busca por título ou descrição"),
    estrutura: str | None = Query(None, description="Filtra por estrutura (UPLOAD, URL, NOTA)"),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Lista recursos com paginação e filtros.
    
    Todos os itens da lista terão o campo `link_acesso` preenchido.

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
    # Carregamento ansioso das tags para a lista
    statement = select(Recurso).options(selectinload(Recurso.tags))
    
    # Filtros de Visibilidade
    if current_user is None or (current_user and current_user.perfil == Perfil.Aluno):
        statement = statement.where(Recurso.visibilidade == Visibilidade.PUBLICO)
    
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

    # Contagem total (Query separada para performance)
    count_statement = select(func.count()).select_from(Recurso)
    
    # Repete filtros para contagem correta
    if current_user is None or (current_user and current_user.perfil == Perfil.Aluno):
        count_statement = count_statement.where(Recurso.visibilidade == Visibilidade.PUBLICO)
    
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

    # Paginação e Ordenação
    offset = (pagination.page - 1) * pagination.per_page
    statement = statement.offset(offset).limit(pagination.per_page).order_by(Recurso.criado_em.desc())
    
    result = await session.exec(statement)
    recursos_db = result.all()

    # CONVERSÃO: Preenche o link de acesso para cada item da lista
    items_dto = [preencher_link_acesso(r) for r in recursos_db]

    total_pages = (total_items + pagination.per_page - 1) // pagination.per_page

    return PaginatedResponse(
        items=items_dto,
        total=total_items,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=total_pages
    )

# ============================================================================
# Endpoints de Escrita
# ============================================================================

@recurso_router.post("/create", response_model=RecursoRead, status_code=status.HTTP_201_CREATED)
async def create_recurso(
    titulo: str = Form(...),
    descricao: str = Form(...),
    estrutura: EstruturaRecurso = Form(...),
    visibilidade: Visibilidade = Form(Visibilidade.PUBLICO),
    is_destaque: bool = Form(False),
    
    # Aceita lista de strings para compatibilidade com Swagger e Postman
    tag_ids: list[str] = Form([]),
    
    # Campos específicos para cada tipo
    file: Optional[UploadFile] = File(None),
    url_externa: Optional[str] = Form(None),
    conteudo_markdown: Optional[str] = Form(None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Cria um novo recurso com suporte a upload de arquivos.
    O retorno inclui o link de acesso gerado.

    Parâmetros:
    - `titulo` (str): Título do recurso.
    - `descricao` (str): Descrição do recurso.
    - `estrutura` (EstruturaRecurso): Tipo do recurso (UPLOAD, URL, NOTA).
    - `visibilidade` (Visibilidade): Visibilidade (PUBLICO, PRIVADO).
    - `is_destaque` (bool): Se o recurso é destaque.
    - `tag_ids` (list[str]): Lista de IDs de tags (aceita "1,2" ou múltiplos campos).
    - `file` (UploadFile|None): Arquivo para upload (obrigatório para UPLOAD).
    - `url_externa` (str|None): URL externa (obrigatória para URL).
    - `conteudo_markdown` (str|None): Conteúdo markdown (obrigatório para NOTA).
    - `session` (AsyncSession): Sessão do banco.
    - `current_user` (User): Usuário autenticado.

    Retorna:
    - `RecursoRead` com os dados do recurso criado (HTTP 201).

    Erros possíveis:
    - 401: Não autenticado.
    - 400: Validação de campos (tipo de arquivo, campos obrigatórios, tags).
    - 413: Arquivo muito grande.
    - 500: Erro no upload.
    """

    # --- PROCESSAMENTO DE TAGS (Swagger Fix) ---
    ids_tags_finais: List[int] = []
    for item in tag_ids:
        # Caso Swagger: "4,1"
        if "," in item:
            partes = item.split(",")
            for p in partes:
                if p.strip().isdigit():
                    ids_tags_finais.append(int(p.strip()))
        # Caso Postman: "4"
        elif item.strip().isdigit():
            ids_tags_finais.append(int(item.strip()))
    ids_tags_finais = list(set(ids_tags_finais)) # Remove duplicatas
    # -------------------------------------------

    # Preparar dados base do recurso
    recurso_data = {
        "titulo": titulo,
        "descricao": descricao,
        "estrutura": estrutura,
        "visibilidade": visibilidade,
        "is_destaque": is_destaque,
        "autor_id": current_user.id,
    }

    # Processar de acordo com o tipo de estrutura
    if estrutura == EstruturaRecurso.UPLOAD:
        if not file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Arquivo é obrigatório para recursos do tipo UPLOAD"
            )
        
        # Fazer upload do arquivo para MinIO
        upload_result = await s3_service.upload_file(file)
        
        recurso_data.update({
            "storage_key": upload_result["storage_key"],
            "mime_type": upload_result["mime_type"],
            "tamanho_bytes": upload_result["tamanho_bytes"],
        })
    elif estrutura == EstruturaRecurso.URL:
        if not url_externa:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URL externa é obrigatória para recursos do tipo URL"
            )
        recurso_data["url_externa"] = url_externa
    elif estrutura == EstruturaRecurso.NOTA:
        if not conteudo_markdown:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Conteúdo markdown é obrigatório para recursos do tipo NOTA"
            )
        recurso_data["conteudo_markdown"] = conteudo_markdown

    # 1. Salva o Recurso
    db_recurso = Recurso.model_validate(recurso_data)
    session.add(db_recurso)
    await session.flush() # Gera o ID do recurso

    # 2. Salva as Tags usando a lista processada
    if ids_tags_finais:
        for tag_id in ids_tags_finais:
            recurso_tag = RecursoTag(
                recurso_id=db_recurso.id,
                tag_id=tag_id
            )
            session.add(recurso_tag)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Erro ao associar tags. Verifique se os IDs existem.")
    
    # 3. Recarrega com tags para retorno (evita erro MissingGreenlet)
    statement = (
        select(Recurso)
        .where(Recurso.id == db_recurso.id)
        .options(selectinload(Recurso.tags))
    )
    result = await session.exec(statement)
    recurso_com_tags = result.one()

    return preencher_link_acesso(recurso_com_tags)

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
    - `RecursoRead` com os dados atualizados e link de acesso.

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
    
    # Reload e Retorno
    statement = (
        select(Recurso)
        .where(Recurso.id == recurso_id)
        .options(selectinload(Recurso.tags))
    )
    result = await session.exec(statement)
    recurso_atualizado = result.one()
    
    return preencher_link_acesso(recurso_atualizado)

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

    # Permissão: apenas autor ou Coordenador podem deletar
    if not (current_user.id == recurso.autor_id or current_user.perfil == Perfil.Coordenador):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão negada para excluir recurso")

    # Se for UPLOAD, remover arquivo do MinIO
    if recurso.estrutura == EstruturaRecurso.UPLOAD and recurso.storage_key:
        try:
            await s3_service.delete_file(recurso.storage_key)
        except Exception as e:
            # Log do erro, mas não falhar a exclusão do banco
            print(f"Erro ao deletar arquivo do S3: {e}")

    await session.delete(recurso)
    await session.commit()

# ============================================================================
# Endpoints de Gerenciamento de Tags
# ============================================================================

@recurso_router.post("/add_tag/{recurso_id}", status_code=status.HTTP_201_CREATED)
async def adicionar_tag_ao_recurso(
    recurso_id: int,
    tag_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Associa uma tag existente a um recurso existente.
    """
    # 1. Verificar se o recurso existe
    statement = select(Recurso).where(Recurso.id == recurso_id)
    result = await session.exec(statement)
    recurso = result.first()

    if not recurso:
        raise HTTPException(status_code=404, detail="Recurso não encontrado")

    # 2. Verificar Permissão (Autor ou Coordenador)
    if not (current_user.id == recurso.autor_id or current_user.perfil == Perfil.Coordenador):
        raise HTTPException(status_code=403, detail="Permissão negada. Apenas autor ou coordenador podem editar.")

    # 3. Verificar se a Tag existe
    tag_statement = select(Tag).where(Tag.id == tag_id)
    tag_result = await session.exec(tag_statement)
    tag = tag_result.first()
    
    if not tag:
        raise HTTPException(status_code=404, detail="Tag não encontrada")

    # 4. Verificar se a associação já existe 
    assoc_statement = select(RecursoTag).where(
        RecursoTag.recurso_id == recurso_id,
        RecursoTag.tag_id == tag_id
    )
    assoc_result = await session.exec(assoc_statement)
    if assoc_result.first():
        raise HTTPException(status_code=400, detail="Esta tag já está associada ao recurso")

    # 5. Criar a associação
    novo_link = RecursoTag(recurso_id=recurso_id, tag_id=tag_id)
    session.add(novo_link)
    await session.commit()

    return {"message": "Tag associada com sucesso"}

@recurso_router.delete("/remove_tag/{recurso_id}/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_tag_do_recurso(
    recurso_id: int,
    tag_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Remove (desassocia) uma tag de um recurso.
    Não apaga a tag do sistema, apenas remove a ligação.
    """
    # 1. Verificar se o recurso existe
    statement = select(Recurso).where(Recurso.id == recurso_id)
    result = await session.exec(statement)
    recurso = result.first()

    if not recurso:
        raise HTTPException(status_code=404, detail="Recurso não encontrado")

    # 2. Verificar Permissão
    if not (current_user.id == recurso.autor_id or current_user.perfil == Perfil.Coordenador):
        raise HTTPException(status_code=403, detail="Permissão negada")

    # 3. Buscar a associação específica
    assoc_statement = select(RecursoTag).where(
        RecursoTag.recurso_id == recurso_id,
        RecursoTag.tag_id == tag_id
    )
    result = await session.exec(assoc_statement)
    link = result.first()

    if not link:
        raise HTTPException(status_code=404, detail="Tag não está associada a este recurso")

    # 4. Deletar a associação
    await session.delete(link)
    await session.commit()