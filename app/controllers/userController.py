from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.dtos.userDtos import UserCreate, UserRead, UserUpdate
from app.enums.perfil import Perfil
from app.enums.status import Status
from app.models.user import User  
from app.core.database import get_session 
from app.core.security import RoleChecker, get_password_hash
from sqlalchemy.exc import IntegrityError 
from fastapi import Query
from app.services.s3_service import s3_service
from app.utils.pagination import PaginationParams
from app.utils.pagination import PaginatedResponse
from app.core.security import get_current_user 
from fastapi import BackgroundTasks 
from app.core.mail import send_activation_email
from app.core.security import create_activation_token
from typing import Optional
from fastapi import UploadFile, File

user_router = APIRouter(prefix="/users", tags=["Users"])

allow_staff = RoleChecker(["Professor", "Coordenador", "Gestor"])
allow_management = RoleChecker(["Coordenador", "Gestor"])
allow_gestor = RoleChecker(["Gestor"])

def preencher_url_perfil(user: User) -> UserRead:
    """
    Converte User (Banco) -> UserRead (DTO) e gera o link do S3.
    """
    # Cria o DTO base
    dto = UserRead.model_validate(user)
    
    # Se tiver path_img, gera o link assinado
    if user.path_img:
        dto.url_perfil = s3_service.get_file_url(user.path_img, download=False)
    else:
        dto.url_perfil = None
        
    return dto

@user_router.get("/get/{user_id}", response_model=UserRead, dependencies=[Depends(allow_staff)])
async def get_user_by_id(user_id: int, session: AsyncSession = Depends(get_session)):
    """Busca um usuário pelo ID.

    Parâmetros:
    - `user_id` (int): ID do usuário a ser buscado.

    Retorna:
    - `UserRead` com os dados do usuário encontrado.

    Erros possíveis:
    - 404: caso o usuário não seja encontrado.
    
    Permissões:
    - Apenas usuários da equipe: 'Professor', 'Cordenador' ou 'Gestor'
    """
    statement = select(User).where(User.id == user_id)
    result = await session.exec(statement)
    user = result.first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return preencher_url_perfil(user)

@user_router.get("/get_all", response_model=PaginatedResponse[UserRead], dependencies=[Depends(allow_staff)])
async def get_all_users(
    session: AsyncSession = Depends(get_session),
    pagination: PaginationParams = Depends(), 
    somente_ativos: bool = Query(True, description="Filtra apenas usuários ativos"),
):
    """Lista usuários com paginação e filtro.

    Parâmetros:
    - `pagination` (PaginationParams): parâmetros de página e itens por página.
    - `somente_ativos` (bool): se True (padrão), retorna apenas usuários com status 'Ativo'.

    Comportamento:
    - Filtra usuários baseados no status (opcional).
    - Calcula o total de páginas e itens para a resposta paginada.

    Retorna:
    - `PaginatedResponse[UserRead]` contendo a lista de usuários e metadados de paginação.
    
    Permissões:
    - Apenas usuários da equipe: 'Professor', 'Cordenador' ou 'Gestor'
    """
    # Montar a query base (sem paginação)
    statement = select(User)
    if somente_ativos:
        statement = statement.where(User.status == Status.Ativo)

    # Contar o total de registros (Query separada)
    count_statement = select(func.count()).select_from(User)
    if somente_ativos:
        count_statement = count_statement.where(User.status == Status.Ativo)
        
    total_result = await session.exec(count_statement)
    total_items = total_result.one()

    # Aplicar a paginação na query principal
    offset = (pagination.page - 1) * pagination.per_page
    
    statement = statement.offset(offset).limit(pagination.per_page).order_by(User.id)
    
    result = await session.exec(statement)
    users = result.all()

    # Calcular total de páginas (para passar pro response)
    total_pages = (total_items + pagination.per_page - 1) // pagination.per_page

    # Retornar a estrutura PaginatedResponse
    return PaginatedResponse(
        items=[preencher_url_perfil(user) for user in users],
        total=total_items,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=total_pages
    )
    
@user_router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)):
    """Retorna os dados do usuário logado.

    Parâmetros:
    - `current_user` (User): usuário autenticado injetado pela dependência.

    Retorna:
    - `UserRead` com os dados do usuário atual.
    
    Permissões:
    - Qualquer usuário autenticado pode acessar esta rota.
    """
    return preencher_url_perfil(current_user)

@user_router.post("/create", response_model=UserRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(allow_management)])
async def create_user(
    user_in: UserCreate, 
    background_tasks: BackgroundTasks, 
    session: AsyncSession = Depends(get_session)
):
    """Cria um novo usuário (Cadastro ou Convite).

    Sendo um cadastro feito por um gestor ou um convite enviado para um novo usuaário, a foto de perfil so pode ser adicionada posteriormente pelo próprio usuário ou por um gestor.

    Parâmetros:
    - `user_in` (UserCreate): dados do novo usuário.

    Comportamento:
    - **Fluxo 1 (Com Senha):** Se a senha for fornecida, cria o usuário como 'Ativo'.
    - **Fluxo 2 (Sem Senha):** Se a senha não for fornecida, define status como 'AguardandoAtivacao', gera token e agenda envio de email de convite.
    - Define avatar como None se não informado.
    
    Perfis:
    - `Gestor`
    - `Coordenador`
    - `Professor`
    - `Aluno`

    Retorna:
    - `UserRead` com os dados do usuário criado (HTTP 201).

    Erros possíveis:
    - 400: se o email já estiver cadastrado.
    
    Permissões:
    - Apenas usuários da gerencia: 'Cordenador' ou 'Gestor'
    """
    user_dict = user_in.model_dump()  
    senha_plana = user_dict.pop("senha", None) 
    
    if senha_plana:
        # Fluxo 1: Gestor definiu a senha manualmente
        user_dict["senha_hash"] = get_password_hash(senha_plana)
        user_dict["status"] = Status.Ativo
    else:
        # Fluxo 2: Gestor não definiu senha, usuário receberá email de ativação
        user_dict["senha_hash"] = None
        user_dict["status"] = Status.AguardandoAtivacao 
        
        token = create_activation_token(user_in.email) # Gerar Token (Jwt específico para ativação)
        background_tasks.add_task(send_activation_email, user_in.email, token) # Agendar envio de email 
        
    if "path_img" not in user_dict:
        user_dict["path_img"] = None

    db_user = User.model_validate(user_dict)
    
    session.add(db_user)
    
    try:
        await session.commit()
        await session.refresh(db_user)
    except IntegrityError:
        await session.rollback() 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Já existe um usuário cadastrado com este email."
        )
        
    return preencher_url_perfil(db_user)

@user_router.post("/resend_invitation/{user_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(allow_management)])
async def resend_invitation(
    user_id: int, 
    background_tasks: BackgroundTasks, 
    session: AsyncSession = Depends(get_session),
):
    """Reenvia o email de convite com token de ativação.

    Comportamento:
    - Busca o usuário pelo ID.
    - **Verificação:** Só permite o reenvio se o status for 'AguardandoAtivacao'.
    - Gera um novo token e agenda o envio do e-mail.

    Erros possíveis:
    - 404: Usuário não encontrado.
    - 400: Usuário já está ativo ou em outro status que não permite reenvio.
    
    Permissões:
    - Apenas usuários da gerencia: 'Cordenador' ou 'Gestor'
    """
    
    user = await session.get(User, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado."
        )

    if user.status != Status.AguardandoAtivacao:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Não é possível reenviar convite. O usuário está com status: {user.status}"
        )

    token = create_activation_token(user.email)
    
    background_tasks.add_task(send_activation_email, user.email, token)

    return {"message": "E-mail de convite reenviado com sucesso."}

@user_router.patch("/patch/{user_id}", response_model=UserRead, dependencies=[Depends(allow_management)])
async def update_user(user_id: int, user_input: UserUpdate, session: AsyncSession = Depends(get_session)):
    """Atualiza dados parciais de um usuário.

    Parâmetros:
    - `user_id` (int): ID do usuário a ser atualizado.
    - `user_input` (UserUpdate): objeto com os campos a serem alterados (campos opcionais).

    Comportamento:
    - Realiza atualização parcial (apenas campos enviados no payload).

    Retorna:
    - `UserRead` com os dados atualizados do usuário.

    Erros possíveis:
    - 404: usuário não encontrado.
    
    Permissões:
    - Apenas usuários da gerencia: 'Cordenador' ou 'Gestor'
    """
    statement = select(User).where(User.id == user_id)
    result = await session.exec(statement)
    db_user = result.first()

    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user_data = user_input.model_dump(exclude_unset=True)

    for key, value in user_data.items():
        setattr(db_user, key, value)

    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return preencher_url_perfil(db_user)


@user_router.patch("/{user_id}/image", status_code=status.HTTP_200_OK)
async def update_user_profile_image(
    user_id: int,
    file: Optional[UploadFile] = File(None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Atualiza ou remove a imagem de perfil de um usuário específico.
    
    Permissões:
    - O próprio usuário pode alterar sua imagem.
    - Um GESTOR pode alterar/remover a imagem de qualquer usuário (moderação).
    
    Comportamento:
    - Se enviar arquivo (`file`): Substitui a imagem atual pela nova.
    - Se NÃO enviar arquivo: Remove a imagem atual (útil para moderação).
    """

    # 1. Buscar o usuário alvo
    statement = select(User).where(User.id == user_id)
    result = await session.exec(statement)
    target_user = result.first()

    if not target_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # 2. Verificar Permissões (Próprio usuário OU Gestor)
    is_self = current_user.id == target_user.id
    is_gestor = current_user.perfil == Perfil.Gestor
    
    if not (is_self or is_gestor):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Permissão negada. Você não pode alterar a imagem deste usuário."
        )

    # 3. Se o usuário alvo JÁ tem uma foto, deletamos ela do S3 primeiro.
    if target_user.path_img:
        try:
            await s3_service.delete_file(target_user.path_img)
        except Exception as e:
            print(f"Aviso: Erro ao limpar imagem antiga do S3: {e}")

    url_visualizacao = None
    msg = ""

    # 4. Atualizar ou Remover
    if file:
        upload_result = await s3_service.upload_file(file)
        target_user.path_img = upload_result["storage_key"]
        url_visualizacao = s3_service.get_file_url(target_user.path_img, download=False)
        msg = "Imagem de perfil atualizada com sucesso."
    else:
        target_user.path_img = None
        msg = "Imagem de perfil removida com sucesso."

    # 5. Salva no Banco
    session.add(target_user)
    await session.commit()
    await session.refresh(target_user)

    return {
        "message": msg,
        "user_id": target_user.id,
        "url_perfil": url_visualizacao
    }

@user_router.patch("/restore/{user_id}", response_model=UserRead, dependencies=[Depends(allow_gestor)])
async def restore_user(
    user_id: int, 
    session: AsyncSession = Depends(get_session)
):
    """
    Restaura um usuário que foi excluído logicamente (Soft Delete).
    Transição: Inativo -> Ativo.
    
    Parâmetros:
    - `user_id` (int): ID do usuário.

    Comportamento:
    - Passa de 'Inativo' para 'Ativo'.

    Retorna:
    - `UserRead`.

    Erros possíveis:
    - 404: usuário não encontrado.
    
    Permissões:
    - Apenas 'Gestor'
    """
    
    user = await session.get(User, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Usuário não encontrado."
        )

    if user.status != Status.Inativo:
        if user.status == Status.Ativo:
            detail_msg = "Este usuário já está ativo."
        elif user.status == Status.AguardandoAtivacao:
            detail_msg = "Este usuário nunca foi ativado. Reenvie o convite em vez de restaurar."
            
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ação inválida. {detail_msg}"
        )

    user.status = Status.Ativo
    
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    return preencher_url_perfil(user)

@user_router.delete("/delete/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(allow_gestor)])
async def delete_user(user_id: int, session: AsyncSession = Depends(get_session)):
    """Remove ou desativa um usuário (Delete Híbrido).

    Parâmetros:
    - `user_id` (int): ID do usuário a ser excluído.

    Comportamento:
    - **Hard Delete:** Se o status for 'AguardandoAtivacao', remove o registro fisicamente do banco.
    - **Soft Delete:** Para outros status, altera o status para 'Inativo' mantendo o histórico.

    Retorna:
    - Nada (HTTP 204 No Content).

    Erros possíveis:
    - 404: usuário não encontrado.
    
    Permissões:
    - Apenas 'Gestor'
    """
    statement = select(User).where(User.id == user_id)
    
    result = await session.exec(statement)
    user = result.first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if user.status == Status.AguardandoAtivacao:
        # HARD DELETE: Remove o registro fisicamente do banco
        await session.delete(user)
    else:
        # SOFT DELETE: Apenas altera o status, mantendo o histórico
        user.status = Status.Inativo
        session.add(user)
    
    await session.commit()