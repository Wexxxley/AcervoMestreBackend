# � Acervo Mestre - Backend

O **Acervo Mestre** é uma plataforma robusta para gestão de recursos educacionais, permitindo o armazenamento, categorização e compartilhamento de materiais em diversos formatos (Upload, URL externa ou Notas em Markdown).

Este guia contém o passo a passo para configurar o ambiente de desenvolvimento local e informações sobre a arquitetura do sistema.

-----

## 🛠️ Tecnologias Utilizadas

* **Framework:** [FastAPI](https://fastapi.tiangolo.com/) - Alta performance e tipagem Python moderna
* **ORM:** [SQLModel](https://sqlmodel.tiangolo.com/) - A união perfeita entre SQLAlchemy e Pydantic
* **Banco de Dados:** PostgreSQL (Hospedado via **Neon.tech** em produção)
* **Storage:** 
  * **MinIO/S3:** Para armazenamento local/privado de arquivos
  * **Supabase Storage:** Para distribuição escalável de assets
* **Segurança:** OAuth2 com JWT (JSON Web Tokens)
* **Migrations:** Alembic para versionamento do banco de dados
* **Testes:** Pytest com cobertura automatizada

-----

## 🏗️ Arquitetura do Sistema

O projeto segue uma estrutura modular para facilitar a manutenção e escalabilidade:

```text
app/
├── controllers/    # Endpoints da API divididos por módulos
├── core/          # Configurações globais (Segurança, DB, Injeção)
├── dtos/          # Data Transfer Objects (Schemas Pydantic)
├── enums/         # Enumerações (Perfis, Visibilidade, Estrutura)
├── models/        # Definições das tabelas do banco (SQLModel)
├── services/      # Lógica de negócio e integrações externas (S3, Supabase)
└── utils/         # Funções auxiliares (Paginação, Formatação)
```

-----

## 📊 Modelo de Dados (Métricas e Relacionamentos)

O sistema foi desenhado para suportar alta interação. Cada recurso possui rastreamento dinâmico de performance e taxonomia organizada:

* **Visualizações:** Incrementadas automaticamente a cada acesso detalhado
* **Downloads:** Rastreamento de cliques em arquivos de upload via endpoint dedicado
* **Curtidas:** Sistema de feedback para engajamento da comunidade
* **Tags:** Relacionamento **N:N** via `RecursoTag` para filtragem avançada

-----

## 🔑 Níveis de Acesso (RBAC)

A API utiliza um sistema de `RoleChecker` personalizado para proteger as rotas com base no perfil do usuário:

| Perfil | Permissões |
|---|---|
| **Aluno** | Acesso apenas a recursos com visibilidade `PÚBLICO` |
| **Professor** | Criação de recursos, gestão de tags e seus próprios materiais |
| **Coordenador** | Moderação de recursos, edição de qualquer material e gestão de staff |
| **Gestor** | Acesso administrativo total e configurações de sistema |

-----

## 🌐 API ao Vivo e Documentação

O backend está implantado e pode ser testado diretamente pelo Swagger UI:

🔗 **[Documentação Interativa (Swagger)](https://acervomestrebackend.onrender.com/docs#/)**

### 🔓 Como realizar o Login (Ambiente de Teste)

Para testar os endpoints protegidos (POST, PATCH, DELETE), siga estes passos:

1. Acesse o link da documentação acima
2. Vá no endpoint **Auth/login** e use as credenciais:
   * **Email:** `admin@acervomestre.com`
   * **Senha:** `Admin@123`
3. Copie o `access_token` retornado
4. Clique no botão **Authorize** (cadeado) no topo da página
5. Cole o token no campo e clique em **Authorize**
6. Após autorizar, todos os endpoints estarão liberados conforme o perfil de Gestor

### 📌 Principais Endpoints

#### Recursos
* `GET /recursos/get_all` - Lista recursos com paginação e filtros
* `GET /recursos/get/{recurso_id}` - Detalhes de um recurso específico
* `POST /recursos/create` - Criar novo recurso (requer autenticação)
* `POST /recursos/upload/supabase` - Upload de arquivo para Supabase
* `PATCH /recursos/patch/{recurso_id}` - Atualizar recurso
* `DELETE /recursos/delete/{recurso_id}` - Excluir recurso

#### Métricas e Interação
* `POST /recursos/{recurso_id}/download` - Registrar download de recurso
* `POST /recursos/{recurso_id}/like` - Curtir um recurso (requer autenticação)

#### Tags
* `POST /recursos/add_tag/{recurso_id}` - Associar tag a recurso
* `DELETE /recursos/remove_tag/{recurso_id}/{tag_id}` - Remover associação

#### Autenticação
* `POST /auth/login` - Login com email e senha
* `POST /auth/register` - Registro de novo usuário
* `GET /auth/me` - Informações do usuário autenticado

-----

## 🚀 Pré-requisitos

Antes de começar, certifique-se de ter instalado:

  * [Python 3.10+](https://www.python.org/downloads/)
  * [Docker Desktop](https://www.docker.com/products/docker-desktop/)
  * [Git](https://git-scm.com/)

-----

## 🛠️ Instalação e Configuração

Siga os passos abaixo na ordem para rodar o projeto.

### 1\. Clonar e preparar o Python

```bash
# Clone o repositório
git clone https://github.com/Wexxxley/AcervoMestreBackend
cd AcervoMestre

# Crie o ambiente virtual
python -m venv venv

# Ative o ambiente virtual:
.\venv\Scripts\activate # Windows
source venv/bin/activate # Linux/Mac

# Instale as dependências
pip install -r requirements.txt
```

### 2\. Configurar Variáveis de Ambiente (`.env`)

Crie um arquivo chamado `.env` na raiz do projeto.

```ini
# .env
DATABASE_URL=postgresql+asyncpg://user_acervo:senha_segura@localhost:5432/acervo_mestre_db
```

> **⚠️ Atenção:** O arquivo `.env` nunca deve ser enviado para o Git (ele já está no `.gitignore`). Cada desenvolvedor tem o seu local.

### 3\. Subir o Banco de Dados (Docker)

Não é necessário instalar o PostgreSQL na sua máquina.

```bash
# Na raiz do projeto, rode:
docker compose up -d
```

*Isso vai baixar a imagem do Postgres e iniciar o banco na porta 5432.*

### 4\. Criar as Tabelas (Migrations)

Usamos o **Alembic** para gerenciar o banco. Para criar as tabelas no seu banco local:

```bash
alembic upgrade head
```

-----

## ▶️ Rodando a Aplicação

Com o banco rodando e as dependências instaladas:

```bash
uvicorn main:app
```

-----

## 🤝 Fluxo de Trabalho em Equipe (IMPORTANTE)

Para evitar conflitos no banco de dados, siga estas regras ao criar novas funcionalidades:

### 1\. Criando uma nova Tabela ou Campo

Sempre que você criar um **novo arquivo de modelo** em `app/models/` ou alterar um existente, siga este fluxo:

1.  **Atualize o Código:** Garanta que você tem a versão mais atual (`git pull`).

2.  **⚠️ REGISTRE O MODELO:**
    Se você criou um **arquivo novo** (ex: `app/models/tag.py`), você **DEVE** importá-lo no arquivo `alembic/env.py` para que o Alembic o reconheça.

    *Abra `alembic/env.py` e adicione:*

    ```python
    from app.models.user import User
    from app.models.produto import tag
    ```

3.  **Gere a Migration:**

    ```bash
    alembic revision --autogenerate -m "cria tabela produto"
    ```

4.  **Aplique:**

    ```bash
    alembic upgrade head
    ```

### 2\. Baixando atualizações dos colegas

Quando você fizer um `git pull` e vierem novas migrations criadas por outros membros da equipe:

1.  Rode o comando para atualizar seu banco local:
    ```bash
    alembic upgrade head
    ```

### 3\. Instalando novas dependências

Se alguém instalar uma biblioteca nova, o arquivo `requirements.txt` será atualizado. Sempre que baixar atualizações, rode:

```bash
pip install -r requirements.txt
```

---

## 🧪 Testes Automatizados

Utilizamos o **Pytest** para garantir a qualidade do código. O ambiente de testes é configurado automaticamente para usar um banco de dados em memória (SQLite), garantindo que os testes não afetem o banco de desenvolvimento.

### 1\. Rodando a Suite de Testes

Para executar todos os testes do projeto, basta rodar na raiz:

```bash
pytest tests/
```

Para rodar apenas um arquivo específico:

```bash
pytest tests/controllers/test_user_controller.py -v
```