# ✅ Compatibilidade de Funcionalidades - MinIO vs Supabase

## Resumo

**Todas as funcionalidades de recursos agora suportam tanto MinIO (desenvolvimento) quanto Supabase (produção)** de forma automática! 🎉

## 🔄 Detecção Automática

O sistema detecta automaticamente qual storage está sendo usado através do `storage_key`:

```python
if storage_key.startswith("http"):
    # É Supabase - URL completa
    # Exemplo: https://...supabase.co/storage/v1/object/public/recursos/abc123.pdf
else:
    # É MinIO - apenas a chave
    # Exemplo: abc123.pdf
```

## 📊 Funcionalidades Suportadas

| Funcionalidade | Endpoint | MinIO ✅ | Supabase ✅ | Compatível |
|---------------|----------|----------|-------------|------------|
| **Criar Recurso (Upload)** | `POST /recursos/create` | ✅ | ✅ | ✅ Automático |
| **Upload Supabase** | `POST /recursos/upload/supabase` | ❌ | ✅ | ✅ Específico |
| **Listar Recursos** | `GET /recursos/get_all` | ✅ | ✅ | ✅ Agnóstico |
| **Buscar por ID** | `GET /recursos/get/{id}` | ✅ | ✅ | ✅ Agnóstico |
| **Atualizar Recurso** | `PATCH /recursos/patch/{id}` | ✅ | ✅ | ✅ Agnóstico |
| **Deletar Recurso** | `DELETE /recursos/delete/{id}` | ✅ | ✅ | ✅ Automático |
| **Download/URL** | `POST /recursos/{id}/download` | ✅ | ✅ | ✅ Automático |

## 🔍 Detalhes de Implementação

### 1. Upload (Criar)

#### MinIO (Desenvolvimento)
```python
# POST /recursos/create
# storage_key: "abc123.pdf"
await s3_service.upload_file(file)
```

#### Supabase (Produção)
```python
# POST /recursos/upload/supabase
# storage_key: "https://...supabase.co/.../abc123.pdf"
await supabase_storage_service.upload_file(file)
```

### 2. Download

```python
# Detecção automática
if recurso.storage_key.startswith("http"):
    download_url = recurso.storage_key  # Supabase - já é URL
else:
    download_url = s3_service.get_file_url(recurso.storage_key)  # MinIO
```

### 3. Deletar

```python
# Detecção automática
if recurso.storage_key.startswith("http"):
    # Extrair chave da URL do Supabase
    storage_key_part = recurso.storage_key.split("/")[-1]
    await supabase_storage_service.delete_file(storage_key_part)
else:
    # Usar chave diretamente no MinIO
    await s3_service.delete_file(recurso.storage_key)
```

## 🎯 Cenários de Uso

### Desenvolvimento Local
```bash
# Usa MinIO via Docker
docker-compose up -d

# Upload via endpoint tradicional
POST /recursos/create
# storage_key: "abc123.pdf"
```

### Produção
```bash
# Usa Supabase (nuvem)
# Configurar .env com credenciais Supabase

# Upload via endpoint Supabase
POST /recursos/upload/supabase
# storage_key: "https://...supabase.co/.../abc123.pdf"
```

### Híbrido (Migração)
```bash
# Pode ter recursos em ambos os storages!
# - Recursos antigos: MinIO (chave simples)
# - Recursos novos: Supabase (URL completa)
# 
# Todas as operações funcionam corretamente! ✅
```

## ⚙️ Configuração

### MinIO (Docker)
```env
# .env
AWS_ACCESS_KEY_ID=admin
AWS_SECRET_ACCESS_KEY=password123
S3_BUCKET_NAME=acervo-mestre
S3_ENDPOINT_URL=http://localhost:9000
S3_REGION=us-east-1
```

### Supabase (Nuvem)
```env
# .env
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-chave-publica
SUPABASE_BUCKET_NAME=recursos
```

## 🧪 Testes

### Executar Testes
```bash
# Todos os testes de recursos
pytest tests/test_recursos.py -v

# Testes específicos do Supabase
pytest tests/test_recursos_supabase.py -v

# Com coverage
pytest tests/test_recursos*.py --cov=app/controllers --cov=app/services
```

### Testar Manualmente

#### 1. MinIO (Local)
```bash
# Subir o MinIO
docker-compose up -d minio

# Testar upload
curl -X POST "http://localhost:8000/recursos/create" \
  -H "Authorization: Bearer $TOKEN" \
  -F "titulo=Teste MinIO" \
  -F "descricao=Upload local" \
  -F "estrutura=UPLOAD" \
  -F "file=@arquivo.pdf"
```

#### 2. Supabase (Nuvem)
```bash
# Testar conexão
python scripts/test_supabase.py

# Testar upload
curl -X POST "http://localhost:8000/recursos/upload/supabase" \
  -H "Authorization: Bearer $TOKEN" \
  -F "titulo=Teste Supabase" \
  -F "descricao=Upload nuvem" \
  -F "arquivo=@arquivo.pdf"
```

## 🐛 Troubleshooting

### Erro no Delete do Supabase
```
Erro ao deletar arquivo do storage: ...
```
**Causa**: O bucket do Supabase pode estar configurado como somente leitura.
**Solução**: No dashboard do Supabase, vá em Storage > seu_bucket > Policies e adicione política de DELETE.

### Erro no Download do MinIO
```
URL inválida ou não acessível
```
**Causa**: MinIO não está rodando ou bucket não existe.
**Solução**: 
```bash
docker-compose up -d minio createbuckets
```

### Storage Key Inválida
```
Recurso de upload sem storage_key
```
**Causa**: Migração incompleta ou recurso criado antes da implementação.
**Solução**: Deletar e recriar o recurso.

## 📈 Métricas de Compatibilidade

- ✅ **100% das funcionalidades** suportam ambos os storages
- ✅ **Detecção automática** - sem necessidade de configuração manual
- ✅ **Zero breaking changes** - código existente continua funcionando
- ✅ **Migração gradual** - pode ter recursos em ambos os storages
- ✅ **Fallback gracioso** - erros de storage não quebram a aplicação

## 🚀 Próximos Passos

1. ✅ Todas as funcionalidades compatíveis
2. ⏳ Deploy do backend (Render/Railway)
3. ⏳ Configurar CORS para frontend
4. ⏳ Testar integração end-to-end
5. ⏳ Monitoramento e logs

## 📚 Documentação Adicional

- [SUPABASE_UPLOAD.md](SUPABASE_UPLOAD.md) - Guia completo de upload
- [test_recursos_supabase.py](../tests/test_recursos_supabase.py) - Testes automatizados
- [supabase_storage_service.py](../app/services/supabase_storage_service.py) - Implementação do serviço
