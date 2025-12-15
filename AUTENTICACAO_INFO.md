# 🔐 Autenticação no Módulo de Recursos

## Situação Atual

O módulo de Recursos está **totalmente implementado**, mas a autenticação JWT ainda não foi implementada. Por isso, criamos **duas formas de usar o sistema**:

## 📋 Opções de Uso

### Opção 1: Modo Sem Autenticação (Apenas Leitura)

**Quando usar:** Para testar listagem e visualização de recursos públicos.

**Configuração em `app/core/security.py`:**
```python
async def get_current_user(...) -> User | None:
    return None  # ← Descomente esta linha
```

**O que funciona:**
- ✅ GET /recursos/get_all (recursos PUBLICOS)
- ✅ GET /recursos/get/{id} (recursos PUBLICOS)
- ✅ POST /recursos/{id}/download (recursos PUBLICOS)

**O que NÃO funciona:**
- ❌ POST /recursos/create
- ❌ PATCH /recursos/patch/{id}
- ❌ DELETE /recursos/delete/{id}
- ❌ Acesso a recursos PRIVADOS

---

### Opção 2: Modo Mock (Usuário Automático) ⭐ RECOMENDADO PARA TESTES

**Quando usar:** Para testar TODAS as funcionalidades do módulo sem implementar JWT.

**Configuração em `app/core/security.py`:**
```python
async def get_current_user(...) -> User | None:
    # Busca o primeiro Professor/Coordenador do banco
    statement = select(User).where(User.perfil == Perfil.Professor).limit(1)
    result = await session.exec(statement)
    return result.first()  # ← Retorna usuário real do banco
```

**O que funciona:**
- ✅ **TODAS** as rotas
- ✅ Criar recursos (autor_id = usuário mock)
- ✅ Editar recursos (se for o autor)
- ✅ Deletar recursos (se for o autor)
- ✅ Ver recursos PRIVADOS (Professor pode ver)

**Requisitos:**
1. Ter pelo menos 1 usuário Professor ou Coordenador no banco
2. Se não tiver, criar via POST /users/create

---

## 🚀 Como Testar Agora

### 1. Verificar se tem usuários no banco

```bash
# Via Python
python -c "
import asyncio
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.core.database import engine
from app.models.user import User

async def check():
    async with AsyncSession(engine) as session:
        result = await session.exec(select(User))
        users = result.all()
        print(f'Usuários no banco: {len(users)}')
        for u in users:
            print(f'  - {u.nome} ({u.perfil})')

asyncio.run(check())
"
```

### 2. Se não tiver usuários, criar um

**Via Swagger UI (http://localhost:8000/docs):**

```json
POST /users/create
{
  "nome": "Professor Teste",
  "email": "professor@teste.com",
  "senha": "senha123",
  "perfil": "Professor",
  "data_nascimento": "1990-01-01"
}
```

**Ou via cURL:**
```bash
curl -X POST "http://localhost:8000/users/create" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Professor Teste",
    "email": "professor@teste.com",
    "senha": "senha123",
    "perfil": "Professor",
    "data_nascimento": "1990-01-01"
  }'
```

### 3. Testar criação de recurso

```bash
curl -X POST "http://localhost:8000/recursos/create" \
  -F "titulo=Teste de Nota" \
  -F "descricao=Descrição do recurso" \
  -F "estrutura=NOTA" \
  -F "visibilidade=PUBLICO" \
  -F "conteudo_markdown=# Conteúdo da nota"
```

---

## 🔧 Implementação JWT Real (Futuro)

Quando implementar autenticação JWT, será necessário:

### 1. Criar endpoint de login

```python
@app.post("/auth/login")
async def login(credentials: LoginDTO, session: AsyncSession):
    # Validar email/senha
    user = await get_user_by_email(session, credentials.email)
    if not user or not verify_password(credentials.senha, user.senha_hash):
        raise HTTPException(401, "Credenciais inválidas")
    
    # Gerar token JWT
    token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}
```

### 2. Atualizar get_current_user

```python
from fastapi.security import OAuth2PasswordBearer
import jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session)
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        statement = select(User).where(User.id == int(user_id))
        result = await session.exec(statement)
        user = result.first()
        
        if not user:
            raise HTTPException(401, "Usuário não encontrado")
        
        return user
    except jwt.JWTError:
        raise HTTPException(401, "Token inválido")
```

### 3. Adicionar dependência opcional

Para rotas que funcionam com ou sem autenticação (ver recursos públicos):

```python
async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
    session: AsyncSession = Depends(get_session)
) -> User | None:
    if not credentials:
        return None
    
    try:
        # Decodificar token
        return await get_current_user(credentials.credentials, session)
    except:
        return None
```

---

## 📊 Tabela de Comparação

| Funcionalidade | Sem Autenticação | Mock User | JWT Real |
|----------------|------------------|-----------|----------|
| Ver públicos | ✅ | ✅ | ✅ |
| Ver privados | ❌ | ✅ | ✅ |
| Criar | ❌ | ✅ | ✅ |
| Editar | ❌ | ✅ (como mock) | ✅ (como token) |
| Deletar | ❌ | ✅ (como mock) | ✅ (como token) |
| Controle fino | ❌ | ⚠️ (todos como mock) | ✅ (por usuário) |
| Produção | ❌ | ❌ | ✅ |

---

## ⚠️ Avisos Importantes

### Para Desenvolvimento (Mock User)
- ✅ Perfeito para testar funcionalidades
- ✅ Não precisa fazer login
- ⚠️ Todos os recursos são criados pelo mesmo usuário mock
- ❌ NÃO usar em produção

### Para Produção
- ❌ **NUNCA** deixar modo mock ativo
- ✅ Implementar JWT antes de deploy
- ✅ Usar HTTPS
- ✅ Validar tokens em todas as rotas protegidas

---

## 🎯 Resumo

**Para testar AGORA:**
1. Use o modo Mock User (já configurado)
2. Crie um usuário Professor no banco
3. Teste todas as funcionalidades

**Para produção:**
1. Implemente endpoints de autenticação (`/auth/login`, `/auth/register`)
2. Implemente `get_current_user` com JWT
3. Teste com tokens reais
4. Deploy

---

**Status Atual:** ✅ Modo Mock Ativo - Pronto para testes completos!
