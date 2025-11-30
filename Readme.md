# 📚 Acervo Mestre API

Backend do sistema **Acervo Mestre**, desenvolvido com **FastAPI**, **SQLModel** e **PostgreSQL**.

Este guia contém o passo a passo para configurar o ambiente de desenvolvimento local.

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

Sempre que você alterar um arquivo em `app/models/`, você precisa gerar uma *migration*:

1.  Garanta que você tem a versão mais atual do código (`git pull`).
2.  Gere o arquivo de migração:
    ```bash
    alembic revision --autogenerate -m "descricao_da_mudanca"
    ```
3.  Verifique o arquivo gerado em `alembic/versions/` para ver se está tudo certo.
4.  Aplique no seu banco:
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

## 🆘 Solução de Problemas Comuns

**Erro: "Target database is not up to date"**

  * Significa que existem migrations novas que você ainda não rodou.
  * **Solução:** Rode `alembic upgrade head`.

**Erro: "Connection refused"**

  * O banco de dados não está rodando.
  * **Solução:** Verifique se o Docker está aberto e rode `docker compose up -d`.