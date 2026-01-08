# 🔄 Guia Rápido: Storage Híbrido (MinIO + Supabase)

## ✅ Status: Todas as Funcionalidades Compatíveis!

**Sim!** Todas as funcionalidades de recursos funcionam tanto com MinIO quanto com Supabase. O sistema detecta automaticamente qual storage usar.

## 📋 Checklist de Funcionalidades

### ✅ Upload
- [x] MinIO: `POST /recursos/create` com `estrutura=UPLOAD`
- [x] Supabase: `POST /recursos/upload/supabase`

### ✅ Download
- [x] Retorna URL correta para MinIO (gera URL)
- [x] Retorna URL correta para Supabase (já é URL)

### ✅ Delete
- [x] Remove arquivo do MinIO
- [x] Remove arquivo do Supabase

### ✅ Operações de Leitura
- [x] Listar todos os recursos (agnóstico)
- [x] Buscar por ID (agnóstico)
- [x] Buscar por filtros (agnóstico)

### ✅ Atualização
- [x] Atualizar metadados (agnóstico)

## 🎯 Como Usar

### Desenvolvimento (MinIO)
```bash
# 1. Subir o Docker
docker-compose up -d

# 2. Usar endpoint tradicional
POST /recursos/create
```

### Produção (Supabase)
```bash
# 1. Configurar .env com Supabase
SUPABASE_URL=...
SUPABASE_KEY=...

# 2. Usar endpoint específico
POST /recursos/upload/supabase
```

### Híbrido (Ambos)
```bash
# Funciona! Você pode ter:
# - Recursos antigos no MinIO
# - Recursos novos no Supabase
# - Todas as operações funcionam corretamente ✅
```

## 🔍 Como o Sistema Detecta?

```python
# storage_key determina o storage:

# MinIO (chave simples)
storage_key = "abc123.pdf"

# Supabase (URL completa)
storage_key = "https://...supabase.co/.../abc123.pdf"

# Detecção automática:
if storage_key.startswith("http"):
    # Usa Supabase
else:
    # Usa MinIO
```

## ⚡ Exemplo Completo

### 1. Upload para Supabase
```bash
curl -X POST "http://localhost:8000/recursos/upload/supabase" \
  -H "Authorization: Bearer $TOKEN" \
  -F "titulo=Apostila Python" \
  -F "descricao=Material completo" \
  -F "arquivo=@apostila.pdf"
```

**Resposta:**
```json
{
  "id": 1,
  "storage_key": "https://...supabase.co/.../abc123.pdf",
  "mime_type": "application/pdf",
  "tamanho_bytes": 1048576
}
```

### 2. Download (Automático)
```bash
curl -X POST "http://localhost:8000/recursos/1/download" \
  -H "Authorization: Bearer $TOKEN"
```

**Resposta:**
```json
{
  "download_url": "https://...supabase.co/.../abc123.pdf",
  "downloads": 1
}
```

### 3. Deletar (Automático)
```bash
curl -X DELETE "http://localhost:8000/recursos/1/delete" \
  -H "Authorization: Bearer $TOKEN"
```

**Resultado:**
- ✅ Arquivo removido do Supabase
- ✅ Registro removido do banco

## 🧪 Testar Tudo

```bash
# Testar conexão Supabase
python scripts/test_supabase.py

# Testar todos os endpoints
pytest tests/test_recursos*.py -v

# Swagger UI
http://localhost:8000/docs
```

## 📚 Documentação Completa

- [SUPABASE_UPLOAD.md](SUPABASE_UPLOAD.md) - Guia completo
- [STORAGE_COMPATIBILITY.md](STORAGE_COMPATIBILITY.md) - Detalhes técnicos
- [test_recursos_supabase.py](../tests/test_recursos_supabase.py) - Testes

## 🎉 Conclusão

**Sim, todas as funcionalidades funcionam com Supabase!**

Você pode:
- ✅ Fazer upload
- ✅ Fazer download
- ✅ Deletar
- ✅ Listar/buscar
- ✅ Atualizar metadados
- ✅ Usar MinIO e Supabase simultaneamente
