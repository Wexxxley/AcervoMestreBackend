"""
Script para criar um usuário administrador (Gestor) para testes no Swagger.

Uso:
    python scripts/create_admin_user.py
"""
import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import engine
from app.core.security import get_password_hash
from app.models.user import User
from app.enums.perfil import Perfil
from app.enums.status import Status


async def create_admin_user():
    """Cria um usuário administrador (Gestor) para testes."""
    
    # Credenciais do admin
    admin_email = "admin@acervomestre.com"
    admin_password = "Admin@123"
    admin_nome = "Administrador"
    
    async with AsyncSession(engine) as session:
        # Verificar se o usuário já existe
        statement = select(User).where(User.email == admin_email)
        result = await session.exec(statement)
        existing_user = result.first()
        
        if existing_user:
            print(f"❌ Usuário {admin_email} já existe!")
            print(f"📧 Email: {admin_email}")
            print(f"👤 Nome: {existing_user.nome}")
            print(f"🔑 Perfil: {existing_user.perfil.value}")
            return
        
        # Criar novo usuário admin
        admin_user = User(
            nome=admin_nome,
            email=admin_email,
            senha_hash=get_password_hash(admin_password),
            perfil=Perfil.Gestor,
            status=Status.Ativo
        )
        
        session.add(admin_user)
        await session.commit()
        await session.refresh(admin_user)
        
        print("✅ Usuário administrador criado com sucesso!")
        print("\n" + "="*60)
        print("📋 CREDENCIAIS PARA TESTE NO SWAGGER")
        print("="*60)
        print(f"📧 Email:    {admin_email}")
        print(f"🔑 Senha:    {admin_password}")
        print(f"👤 Nome:     {admin_nome}")
        print(f"🎭 Perfil:   {admin_user.perfil.value}")
        print(f"📊 Status:   {admin_user.status.value}")
        print(f"🆔 ID:       {admin_user.id}")
        print("="*60)
        print("\n📝 Como usar no Swagger:")
        print("1. Acesse: http://localhost:8000/docs")
        print("2. Clique em 'Authorize' (cadeado no topo)")
        print("3. Use as credenciais acima para fazer login")
        print("4. Ou use diretamente o endpoint POST /auth/login")
        print("="*60)


async def create_test_users():
    """Cria múltiplos usuários de teste com diferentes perfis."""
    
    test_users = [
        {
            "nome": "Gestor Teste",
            "email": "gestor@test.com",
            "senha": "Gestor@123",
            "perfil": Perfil.Gestor,
        },
        {
            "nome": "Coordenador Teste",
            "email": "coordenador@test.com",
            "senha": "Coord@123",
            "perfil": Perfil.Coordenador,
        },
        {
            "nome": "Professor Teste",
            "email": "professor@test.com",
            "senha": "Prof@123",
            "perfil": Perfil.Professor,
        },
        {
            "nome": "Aluno Teste",
            "email": "aluno@test.com",
            "senha": "Aluno@123",
            "perfil": Perfil.Aluno,
        },
    ]
    
    async with AsyncSession(engine) as session:
        created_users = []
        
        for user_data in test_users:
            # Verificar se já existe
            statement = select(User).where(User.email == user_data["email"])
            result = await session.exec(statement)
            existing = result.first()
            
            if existing:
                print(f"⚠️  {user_data['email']} já existe, pulando...")
                continue
            
            # Criar usuário
            user = User(
                nome=user_data["nome"],
                email=user_data["email"],
                senha_hash=get_password_hash(user_data["senha"]),
                perfil=user_data["perfil"],
                status=Status.Ativo
            )
            
            session.add(user)
            created_users.append((user_data["email"], user_data["senha"], user_data["perfil"]))
        
        if created_users:
            await session.commit()
            
            print("\n✅ Usuários de teste criados com sucesso!")
            print("\n" + "="*60)
            print("📋 CREDENCIAIS DOS USUÁRIOS DE TESTE")
            print("="*60)
            
            for email, senha, perfil in created_users:
                print(f"\n🎭 {perfil.value}")
                print(f"   📧 Email: {email}")
                print(f"   🔑 Senha: {senha}")
            
            print("="*60)
        else:
            print("\n✅ Todos os usuários de teste já existem!")


async def main():
    """Função principal."""
    import sys
    
    print("\n🚀 Criando usuários de teste...\n")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        # Criar múltiplos usuários
        await create_test_users()
    else:
        # Criar apenas o admin
        await create_admin_user()
        print("\n💡 Dica: Use --all para criar usuários de todos os perfis")
        print("   python scripts/create_admin_user.py --all\n")


if __name__ == "__main__":
    asyncio.run(main())
