# Módulo de Recursos - Acervo Mestre

## 📋 Descrição

Este módulo implementa o sistema completo de gerenciamento de recursos educacionais com suporte a três tipos de conteúdo:
- **UPLOAD**: Arquivos (PDF, DOCX, MP4, imagens)
- **URL**: Links externos
- **NOTA**: Conteúdo em Markdown

## 🚀 Como Usar

### 1. Iniciar a Infraestrutura

```bash
# Instalar dependências
pip install -r requirements.txt

# Iniciar containers (PostgreSQL + MinIO)
docker-compose up -d

# Executar migrações
alembic upgrade head

# Iniciar aplicação
uvicorn main:app --reload
```

### 2. Acessar Interfaces

- **API Swagger**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001 (admin/password123)
- **MinIO API**: http://localhost:9000

### 3. Endpoints Disponíveis

#### **POST /recursos/create** - Criar Recurso

**Para Upload de Arquivo:**
```bash
curl -X POST "http://localhost:8000/recursos/create" \
  -H "Content-Type: multipart/form-data" \
  -F "titulo=Meu PDF Educacional" \
  -F "descricao=Material sobre matemática" \
  -F "estrutura=UPLOAD" \
  -F "visibilidade=PUBLICO" \
  -F "file=@/caminho/para/arquivo.pdf"
```

**Para Link Externo:**
```bash
curl -X POST "http://localhost:8000/recursos/create" \
  -H "Content-Type: multipart/form-data" \
  -F "titulo=Vídeo no YouTube" \
  -F "descricao=Aula de física" \
  -F "estrutura=URL" \
  -F "visibilidade=PUBLICO" \
  -F "url_externa=https://youtube.com/watch?v=exemplo"
```

**Para Nota em Markdown:**
```bash
curl -X POST "http://localhost:8000/recursos/create" \
  -H "Content-Type: multipart/form-data" \
  -F "titulo=Resumo da Aula" \
  -F "descricao=Pontos importantes" \
  -F "estrutura=NOTA" \
  -F "visibilidade=PUBLICO" \
  -F "conteudo_markdown=# Título\n\nConteúdo da nota..."
```

#### **GET /recursos/get_all** - Listar Recursos

```bash
# Todos os recursos (com paginação)
curl "http://localhost:8000/recursos/get_all?page=1&per_page=10"

# Filtrar por palavra-chave
curl "http://localhost:8000/recursos/get_all?palavra_chave=matemática"

# Filtrar por tipo
curl "http://localhost:8000/recursos/get_all?estrutura=UPLOAD"
```

#### **GET /recursos/get/{id}** - Buscar Recurso

```bash
curl "http://localhost:8000/recursos/get/1"
```

#### **POST /recursos/{id}/download** - Download/Acesso ao Recurso

```bash
# Para arquivos UPLOAD: retorna URL de download
curl -X POST "http://localhost:8000/recursos/1/download"

# Para URLs: retorna a URL externa
# Para NOTAS: retorna erro (não aplicável)
```

#### **PATCH /recursos/patch/{id}** - Atualizar Recurso

```bash
curl -X PATCH "http://localhost:8000/recursos/patch/1" \
  -H "Content-Type: application/json" \
  -d '{"titulo": "Novo Título", "descricao": "Nova descrição"}'
```

#### **DELETE /recursos/delete/{id}** - Deletar Recurso

```bash
# Remove do banco e do MinIO (se for UPLOAD)
curl -X DELETE "http://localhost:8000/recursos/delete/1"
```

## 🔒 Regras de Permissão

### Visibilidade (RF08)
- **PUBLICO**: Visível para todos (incluindo ALUNO e não autenticados)
- **PRIVADO**: Visível apenas para Professor, Coordenador e Gestor

### Autorização
- **Criar**: Qualquer usuário autenticado
- **Visualizar**: Depende da visibilidade
- **Editar**: Apenas autor ou Coordenador
- **Deletar**: Apenas autor ou Coordenador

## 📁 Estrutura de Arquivos

```
app/
├── controllers/
│   └── recursoController.py      # Rotas da API
├── core/
│   ├── config.py                 # Configurações (S3, limites)
│   ├── database.py               # Conexão PostgreSQL
│   └── security.py               # Autenticação
├── dtos/
│   └── recursoDtos.py            # DTOs (Create, Update, Read, Download)
├── enums/
│   ├── estrutura_recurso.py      # UPLOAD, URL, NOTA
│   ├── visibilidade.py           # PUBLICO, PRIVADO
│   └── perfil.py                 # Gestor, Coordenador, Professor, Aluno
├── models/
│   └── recurso.py                # Model SQLModel
└── services/
    └── s3_service.py             # Integração MinIO/S3
```

## ⚙️ Configuração (.env)

```env
# Database
DATABASE_URL=postgresql+asyncpg://user_acervo:senha_segura@localhost:5432/acervo_mestre_db

# JWT
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# MinIO / S3
AWS_ACCESS_KEY_ID=admin
AWS_SECRET_ACCESS_KEY=password123
S3_BUCKET_NAME=acervo-mestre
S3_ENDPOINT_URL=http://localhost:9000
S3_REGION=us-east-1

# Limites
MAX_FILE_SIZE_MB=100
```

## 🔧 Tipos de Arquivo Permitidos

Por padrão, são aceitos:
- `application/pdf` (PDF)
- `application/vnd.openxmlformats-officedocument.wordprocessingml.document` (DOCX)
- `application/msword` (DOC)
- `video/mp4` (MP4)
- `image/jpeg` (JPEG)
- `image/png` (PNG)
- `image/gif` (GIF)

Para adicionar mais tipos, edite `ALLOWED_MIME_TYPES` em [core/config.py](app/core/config.py).

## 🐛 Troubleshooting

### Erro ao conectar no MinIO
```bash
# Verificar se containers estão rodando
docker-compose ps

# Ver logs do MinIO
docker-compose logs minio

# Recriar containers
docker-compose down
docker-compose up -d
```

### Erro de permissão no bucket
```bash
# Recriar o bucket manualmente
docker exec -it acervo_minio_setup /bin/sh
mc alias set myminio http://minio:9000 admin password123
mc mb myminio/acervo-mestre --ignore-existing
mc anonymous set download myminio/acervo-mestre
```

### Arquivo muito grande
- Ajuste `MAX_FILE_SIZE_MB` em `.env`
- Reinicie a aplicação

## 📊 Métricas de Recursos

Cada recurso rastreia:
- **visualizacoes**: Incrementado ao acessar GET /recursos/get/{id}
- **downloads**: Incrementado ao acessar POST /recursos/{id}/download (apenas UPLOAD)
- **curtidas**: Campo disponível para implementação futura

## 🎯 Próximos Passos

- [ ] Implementar sistema de Tags
- [ ] Adicionar autenticação JWT real
- [ ] Implementar sistema de curtidas
- [ ] Adicionar pré-visualização de arquivos
- [ ] Implementar cache de URLs de download
- [ ] Adicionar suporte a thumbnails

## 📝 Notas Técnicas

- **Single Table Inheritance**: Todos os tipos de recursos compartilham uma única tabela com campos nullable específicos
- **Validação Polimórfica**: DTOs validam que apenas campos relevantes ao tipo sejam preenchidos
- **Storage Keys**: UUIDs únicos previnem conflitos de nome
- **Política Pública**: Bucket configurado com `download` público (leitura anônima)
- **Soft Delete**: Não implementado (exclusão é permanente)
