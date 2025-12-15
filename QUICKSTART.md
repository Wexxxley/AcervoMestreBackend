# 🚀 Guia Rápido - Módulo de Recursos

## ⚡ Início Rápido (3 minutos)

### 1. Configuração Inicial
```bash
# Clone o repositório (se ainda não tiver)
git clone <seu-repo>
cd AcervoMestreBackend

# Copie o arquivo de exemplo
cp .env.example .env

# Instale dependências
pip install -r requirements.txt
```

### 2. Inicie os Serviços
```bash
# Inicie Docker (PostgreSQL + MinIO)
docker-compose up -d

# Execute migrações
alembic upgrade head

# Inicie a API
uvicorn main:app --reload
```

### 3. Crie um usuário para testes
```bash
# O módulo está configurado com um usuário mock automático
# Mas você precisa ter ao menos 1 Professor no banco
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

### 4. Teste a API
Abra no navegador: http://localhost:8000/docs

> **💡 Nota sobre Autenticação:** O módulo está configurado com um "usuário mock" automático para testes. Isso permite testar TODAS as funcionalidades sem implementar JWT. Veja [AUTENTICACAO_INFO.md](AUTENTICACAO_INFO.md) para mais detalhes.

## 📝 Exemplos Rápidos via cURL

### Criar uma Nota
```bash
curl -X POST "http://localhost:8000/recursos/create" \
  -F "titulo=Minha Primeira Nota" \
  -F "descricao=Uma nota de teste" \
  -F "estrutura=NOTA" \
  -F "visibilidade=PUBLICO" \
  -F "conteudo_markdown=# Olá Mundo"
```

### Criar um Link
```bash
curl -X POST "http://localhost:8000/recursos/create" \
  -F "titulo=Vídeo Educacional" \
  -F "descricao=Link para YouTube" \
  -F "estrutura=URL" \
  -F "visibilidade=PUBLICO" \
  -F "url_externa=https://youtube.com/watch?v=exemplo"
```

### Upload de Arquivo (substitua o caminho)
```bash
curl -X POST "http://localhost:8000/recursos/create" \
  -F "titulo=Meu PDF" \
  -F "descricao=Material de estudo" \
  -F "estrutura=UPLOAD" \
  -F "visibilidade=PUBLICO" \
  -F "file=@/caminho/para/arquivo.pdf"
```

### Listar Recursos
```bash
curl "http://localhost:8000/recursos/get_all?page=1&per_page=10"
```

### Buscar Recurso
```bash
curl "http://localhost:8000/recursos/get/1"
```

### Download
```bash
curl -X POST "http://localhost:8000/recursos/1/download"
```

## 🎯 Estrutura dos Dados

### Criar Recurso - Campos por Tipo

#### NOTA
- ✅ titulo (obrigatório)
- ✅ descricao (obrigatório)
- ✅ estrutura = "NOTA" (obrigatório)
- ✅ conteudo_markdown (obrigatório)
- ❌ file (não enviar)
- ❌ url_externa (não enviar)

#### URL
- ✅ titulo (obrigatório)
- ✅ descricao (obrigatório)
- ✅ estrutura = "URL" (obrigatório)
- ✅ url_externa (obrigatório)
- ❌ file (não enviar)
- ❌ conteudo_markdown (não enviar)

#### UPLOAD
- ✅ titulo (obrigatório)
- ✅ descricao (obrigatório)
- ✅ estrutura = "UPLOAD" (obrigatório)
- ✅ file (obrigatório)
- ❌ url_externa (não enviar)
- ❌ conteudo_markdown (não enviar)

### Campos Opcionais (todos os tipos)
- visibilidade (padrão: PUBLICO)
- is_destaque (padrão: false)

## 🔗 URLs Úteis

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| **Swagger UI** | http://localhost:8000/docs | - |
| **MinIO Console** | http://localhost:9001 | admin / password123 |
| **MinIO API** | http://localhost:9000 | - |
| **PostgreSQL** | localhost:5432 | user_acervo / senha_segura |

## 🐛 Troubleshooting

### Erro: "Connection refused" ao conectar no MinIO
```bash
# Verifique se o container está rodando
docker ps

# Reinicie o MinIO
docker-compose restart minio

# Verifique os logs
docker-compose logs minio
```

### Erro: "Bucket not found"
```bash
# Recrie o bucket manualmente
docker exec -it acervo_minio_setup /bin/sh
mc alias set myminio http://minio:9000 admin password123
mc mb myminio/acervo-mestre --ignore-existing
mc anonymous set download myminio/acervo-mestre
exit
```

### Erro: "Type not allowed"
- Verifique se o tipo MIME do arquivo está em `ALLOWED_MIME_TYPES`
- Edite `app/core/config.py` para adicionar mais tipos

### Erro: "File too large"
- Ajuste `MAX_FILE_SIZE_MB` em `.env`
- Padrão: 100MB

## 📊 Scripts Auxiliares

### Windows (PowerShell)
```powershell
.\scripts\dev_commands.ps1
```

### Linux/Mac (Bash)
```bash
chmod +x scripts/dev_commands.sh
./scripts/dev_commands.sh
```

### Python (Testes)
```bash
python scripts/test_recursos.py
```

## 🎓 Entendendo os Perfis

| Perfil | Criar | Ver PUBLICO | Ver PRIVADO | Editar/Deletar |
|--------|-------|-------------|-------------|----------------|
| **Gestor** | ✅ | ✅ | ✅ | ✅ (próprios + coord) |
| **Coordenador** | ✅ | ✅ | ✅ | ✅ (todos) |
| **Professor** | ✅ | ✅ | ✅ | ✅ (próprios) |
| **Aluno** | ✅ | ✅ | ❌ | ✅ (próprios) |
| **Não autenticado** | ❌ | ✅ | ❌ | ❌ |

## 📦 Tipos de Arquivo Suportados

- ✅ PDF (application/pdf)
- ✅ Word (DOCX/DOC)
- ✅ Vídeo MP4 (video/mp4)
- ✅ Imagens (JPEG, PNG, GIF)

## 🎉 Próximos Passos

1. ✅ Criar alguns recursos de teste
2. ✅ Testar filtros e paginação
3. ✅ Testar upload de diferentes tipos
4. 🚧 Implementar autenticação JWT real
5. 🚧 Adicionar sistema de Tags
6. 🚧 Implementar testes automatizados

## 📞 Suporte

- 📖 Documentação completa: [RECURSOS_README.md](RECURSOS_README.md)
- 🏗️ Detalhes da implementação: [IMPLEMENTACAO_RECURSOS.md](IMPLEMENTACAO_RECURSOS.md)
- 🐛 Issues: Abra uma issue no GitHub

---

**Desenvolvido com ❤️ por GitHub Copilot**  
**Projeto: Acervo Mestre - Plataforma Pedagógica**
