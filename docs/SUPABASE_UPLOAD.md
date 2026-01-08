# 🚀 Upload de Arquivos com Supabase Storage

Este documento explica como usar o sistema de upload de recursos utilizando o Supabase Storage.

## 📋 Configuração

### 1. Variáveis de Ambiente

Adicione no arquivo `.env`:

```env
# Configurações Supabase Storage
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-chave-publica-aqui
SUPABASE_BUCKET_NAME=recursos
```

### 2. Criar o Bucket no Supabase

1. Acesse o [Dashboard do Supabase](https://app.supabase.com)
2. Vá em **Storage** no menu lateral
3. Clique em **Create Bucket**
4. Nome do bucket: `recursos`
5. **Marque como "Public bucket"** para gerar URLs públicas
6. Clique em **Create**

### 3. Obter as Credenciais

1. No dashboard do Supabase, vá em **Settings** > **API**
2. Copie:
   - **Project URL** → `SUPABASE_URL`
   - **Project API keys** → `anon public` → `SUPABASE_KEY`

### 4. Testar a Conexão

Execute o script de teste:

```bash
python scripts/test_supabase.py
```

Você deve ver:
```
✅ Cliente Supabase criado com sucesso!
✅ Bucket 'recursos' encontrado!
🎉 Conexão com Supabase Storage OK!
```

## 🎯 Como Usar

### Endpoint: `POST /recursos/upload/supabase`

Este endpoint implementa o **[RF04] - Cadastrar Recurso (Upload)**.

#### Requisição

**Headers:**
```
Authorization: Bearer {seu_token_jwt}
Content-Type: multipart/form-data
```

**Form Data:**
- `titulo` (string, obrigatório): Título do recurso
- `descricao` (string, obrigatório): Descrição do recurso
- `visibilidade` (string, opcional): `PUBLICO` ou `PRIVADO` (padrão: `PUBLICO`)
- `is_destaque` (boolean, opcional): Se o recurso é destaque (padrão: `false`)
- `arquivo` (file, obrigatório): Arquivo para upload

#### Exemplo com cURL

```bash
curl -X POST "http://localhost:8000/recursos/upload/supabase" \
  -H "Authorization: Bearer seu_token_aqui" \
  -F "titulo=Apostila de Python" \
  -F "descricao=Material completo sobre Python básico" \
  -F "visibilidade=PUBLICO" \
  -F "is_destaque=true" \
  -F "arquivo=@/caminho/para/apostila.pdf"
```

#### Exemplo com Python (httpx)

```python
import httpx

url = "http://localhost:8000/recursos/upload/supabase"
token = "seu_token_jwt"

headers = {
    "Authorization": f"Bearer {token}"
}

files = {
    "arquivo": ("apostila.pdf", open("apostila.pdf", "rb"), "application/pdf")
}

data = {
    "titulo": "Apostila de Python",
    "descricao": "Material completo sobre Python básico",
    "visibilidade": "PUBLICO",
    "is_destaque": "true"
}

response = httpx.post(url, headers=headers, files=files, data=data)
print(response.json())
```

#### Resposta de Sucesso (201)

```json
{
  "id": 1,
  "titulo": "Apostila de Python",
  "descricao": "Material completo sobre Python básico",
  "visibilidade": "PUBLICO",
  "estrutura": "UPLOAD",
  "autor_id": 5,
  "is_destaque": true,
  "visualizacoes": 0,
  "downloads": 0,
  "curtidas": 0,
  "storage_key": "https://wwhakuafhtbqthesuclp.supabase.co/storage/v1/object/public/recursos/abc123.pdf",
  "mime_type": "application/pdf",
  "tamanho_bytes": 1048576,
  "url_externa": null,
  "conteudo_markdown": null,
  "criado_em": "2026-01-08T15:30:00Z"
}
```

### Testar no Swagger UI

1. Inicie a aplicação:
   ```bash
   uvicorn main:app --reload
   ```

2. Acesse: http://localhost:8000/docs

3. Clique em **Authorize** e insira seu token JWT

4. Encontre o endpoint **POST /recursos/upload/supabase**

5. Clique em **Try it out**

6. Preencha os campos e selecione um arquivo

7. Clique em **Execute**

## 📊 Arquitetura

### Fluxo de Dados

```
┌─────────┐      ┌──────────────┐      ┌────────────────┐      ┌──────────┐
│ Cliente │─────>│ FastAPI      │─────>│ Supabase       │      │ Neon.tech│
│         │      │ (Controller) │      │ Storage        │      │ (Postgres)│
└─────────┘      └──────────────┘      └────────────────┘      └──────────┘
                        │                      │                      │
                        │  1. Upload arquivo   │                      │
                        │─────────────────────>│                      │
                        │                      │                      │
                        │  2. Retorna URL      │                      │
                        │<─────────────────────│                      │
                        │                                             │
                        │  3. Salva metadados (título, URL, mime, etc)│
                        │────────────────────────────────────────────>│
                        │                                             │
                        │  4. Retorna recurso completo               │
                        │<────────────────────────────────────────────│
```

### Armazenamento

- **Arquivo físico**: Supabase Storage (nuvem)
- **Metadados**: Neon.tech PostgreSQL
  - Tabela `Recurso`: `titulo`, `descricao`, `storage_key` (URL pública), `mime_type`, `tamanho_bytes`, etc.

### Modelo de Dados

```python
class Recurso:
    id: int
    titulo: str
    descricao: str
    visibilidade: Visibilidade  # PUBLICO | PRIVADO
    estrutura: EstruturaRecurso  # UPLOAD | URL | NOTA
    autor_id: int
    is_destaque: bool
    
    # Campos específicos para UPLOAD
    storage_key: str  # URL pública do Supabase
    mime_type: str
    tamanho_bytes: int
    
    # Métricas
    visualizacoes: int
    downloads: int
    curtidas: int
    
    criado_em: datetime
```

## 🔒 Regras de Negócio

### Validações

1. **Tipos de arquivo permitidos** (configurável em `.env`):
   - PDF: `application/pdf`
   - Word: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
   - Vídeo MP4: `video/mp4`
   - Imagens: `image/jpeg`, `image/png`, `image/gif`

2. **Tamanho máximo**: 100 MB (configurável via `MAX_FILE_SIZE_MB`)

3. **Autenticação**: Obrigatória (JWT token)

### Visibilidade

- **PUBLICO**: Qualquer usuário pode visualizar
- **PRIVADO**: Apenas Professores, Coordenadores e Gestores podem visualizar

## 🆚 Comparação: MinIO vs Supabase

| Aspecto | MinIO (Local) | Supabase Storage |
|---------|---------------|------------------|
| **Endpoint** | `/recursos/create` | `/recursos/upload/supabase` |
| **Ambiente** | Desenvolvimento (Docker) | Produção (Nuvem) |
| **URL** | `http://localhost:9000` | `https://...supabase.co` |
| **Persistência** | Local (`minio_data/`) | Nuvem (AWS S3) |
| **URL pública** | Requer configuração | Automática |
| **Custo** | Grátis (local) | Free tier: 1 GB |

## 🐛 Troubleshooting

### Erro: "Tipo de arquivo não permitido"

**Solução**: Adicione o MIME type no `.env`:
```env
ALLOWED_MIME_TYPES=["application/pdf", "video/mp4", "seu_tipo_aqui"]
```

### Erro: "Arquivo muito grande"

**Solução**: Aumente o limite no `.env`:
```env
MAX_FILE_SIZE_MB=200
```

### Erro: "Bucket não encontrado"

**Solução**: 
1. Verifique o nome do bucket no `.env`
2. Certifique-se de que o bucket existe no Supabase
3. Execute `python scripts/test_supabase.py` para diagnosticar

### Erro: "Invalid API key"

**Solução**:
1. Verifique se copiou a chave `anon public` (não a `service_role`)
2. Certifique-se de que não há espaços extras no `.env`

## 📚 Referências

- [Supabase Storage Documentation](https://supabase.com/docs/guides/storage)
- [FastAPI File Uploads](https://fastapi.tiangolo.com/tutorial/request-files/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
