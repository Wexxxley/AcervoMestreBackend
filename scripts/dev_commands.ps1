# Script de comandos úteis para desenvolvimento do módulo de Recursos
# PowerShell Version

function Show-Menu {
    Write-Host ""
    Write-Host "======================================================"
    Write-Host "ACERVO MESTRE - Comandos Úteis"
    Write-Host "======================================================"
    Write-Host ""
    Write-Host "Selecione uma opção:"
    Write-Host "1)  Iniciar todos os serviços (Docker + API)"
    Write-Host "2)  Parar todos os serviços"
    Write-Host "3)  Ver logs do MinIO"
    Write-Host "4)  Ver logs do PostgreSQL"
    Write-Host "5)  Recriar bucket do MinIO"
    Write-Host "6)  Executar migrações do banco"
    Write-Host "7)  Executar testes de recursos"
    Write-Host "8)  Limpar volumes do Docker (CUIDADO!)"
    Write-Host "9)  Instalar dependências Python"
    Write-Host "10) Abrir MinIO Console"
    Write-Host "11) Abrir Swagger UI"
    Write-Host "12) Verificar status dos containers"
    Write-Host "0)  Sair"
    Write-Host ""
}

function Start-Services {
    Write-Host "Iniciando serviços..." -ForegroundColor Green
    docker-compose up -d
    Write-Host "Aguardando MinIO inicializar..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    Write-Host "Serviços iniciados!" -ForegroundColor Green
    Write-Host "Para iniciar a API, execute em outro terminal:" -ForegroundColor Cyan
    Write-Host "uvicorn main:app --reload" -ForegroundColor White
}

function Stop-Services {
    Write-Host "Parando serviços..." -ForegroundColor Yellow
    docker-compose down
    Write-Host "Serviços parados." -ForegroundColor Green
}

function View-MinioLogs {
    Write-Host "Logs do MinIO (Ctrl+C para sair):" -ForegroundColor Cyan
    docker-compose logs -f minio
}

function View-PostgresLogs {
    Write-Host "Logs do PostgreSQL (Ctrl+C para sair):" -ForegroundColor Cyan
    docker-compose logs -f db
}

function Recreate-Bucket {
    Write-Host "Recriando bucket acervo-mestre..." -ForegroundColor Yellow
    docker exec -it acervo_minio_setup /bin/sh -c @"
        mc alias set myminio http://minio:9000 admin password123
        mc mb myminio/acervo-mestre --ignore-existing
        mc anonymous set download myminio/acervo-mestre
"@
    Write-Host "Bucket recriado com sucesso!" -ForegroundColor Green
}

function Run-Migrations {
    Write-Host "Executando migrações do Alembic..." -ForegroundColor Yellow
    alembic upgrade head
    Write-Host "Migrações concluídas!" -ForegroundColor Green
}

function Run-Tests {
    Write-Host "Executando testes de recursos..." -ForegroundColor Yellow
    python scripts/test_recursos.py
}

function Clean-Volumes {
    Write-Host "AVISO: Isso irá apagar TODOS os dados!" -ForegroundColor Red
    $confirm = Read-Host "Tem certeza? (yes/no)"
    if ($confirm -eq "yes") {
        docker-compose down -v
        Remove-Item -Recurse -Force postgres_data/ -ErrorAction SilentlyContinue
        Remove-Item -Recurse -Force minio_data/ -ErrorAction SilentlyContinue
        Write-Host "Volumes limpos!" -ForegroundColor Green
    } else {
        Write-Host "Operação cancelada." -ForegroundColor Yellow
    }
}

function Install-Dependencies {
    Write-Host "Instalando dependências Python..." -ForegroundColor Yellow
    pip install -r requirements.txt
    Write-Host "Dependências instaladas!" -ForegroundColor Green
}

function Open-MinioConsole {
    Write-Host "Abrindo MinIO Console..." -ForegroundColor Cyan
    Write-Host "URL: http://localhost:9001" -ForegroundColor White
    Write-Host "Usuário: admin" -ForegroundColor White
    Write-Host "Senha: password123" -ForegroundColor White
    Start-Process "http://localhost:9001"
}

function Open-SwaggerUI {
    Write-Host "Abrindo Swagger UI..." -ForegroundColor Cyan
    Write-Host "URL: http://localhost:8000/docs" -ForegroundColor White
    Start-Process "http://localhost:8000/docs"
}

function Check-ContainerStatus {
    Write-Host "Status dos containers:" -ForegroundColor Cyan
    docker-compose ps
}

# Loop principal
while ($true) {
    Show-Menu
    $option = Read-Host "Opção"
    
    switch ($option) {
        "1"  { Start-Services }
        "2"  { Stop-Services }
        "3"  { View-MinioLogs }
        "4"  { View-PostgresLogs }
        "5"  { Recreate-Bucket }
        "6"  { Run-Migrations }
        "7"  { Run-Tests }
        "8"  { Clean-Volumes }
        "9"  { Install-Dependencies }
        "10" { Open-MinioConsole }
        "11" { Open-SwaggerUI }
        "12" { Check-ContainerStatus }
        "0"  { Write-Host "Saindo..." -ForegroundColor Green; exit 0 }
        default { Write-Host "Opção inválida!" -ForegroundColor Red }
    }
}
