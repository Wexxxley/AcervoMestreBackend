#!/bin/bash
# Script de comandos úteis para desenvolvimento do módulo de Recursos

echo "======================================================"
echo "ACERVO MESTRE - Comandos Úteis"
echo "======================================================"

show_menu() {
    echo ""
    echo "Selecione uma opção:"
    echo "1) Iniciar todos os serviços (Docker + API)"
    echo "2) Parar todos os serviços"
    echo "3) Ver logs do MinIO"
    echo "4) Ver logs do PostgreSQL"
    echo "5) Recriar bucket do MinIO"
    echo "6) Executar migrações do banco"
    echo "7) Executar testes de recursos"
    echo "8) Limpar volumes do Docker (CUIDADO!)"
    echo "9) Instalar dependências Python"
    echo "10) Abrir MinIO Console"
    echo "11) Abrir Swagger UI"
    echo "0) Sair"
    echo ""
}

start_services() {
    echo "Iniciando serviços..."
    docker-compose up -d
    echo "Aguardando MinIO inicializar..."
    sleep 5
    echo "Iniciando API FastAPI..."
    echo "Execute em outro terminal: uvicorn main:app --reload"
}

stop_services() {
    echo "Parando serviços..."
    docker-compose down
    echo "Serviços parados."
}

view_minio_logs() {
    echo "Logs do MinIO:"
    docker-compose logs -f minio
}

view_postgres_logs() {
    echo "Logs do PostgreSQL:"
    docker-compose logs -f db
}

recreate_bucket() {
    echo "Recriando bucket acervo-mestre..."
    docker exec -it acervo_minio_setup /bin/sh -c "
        mc alias set myminio http://minio:9000 admin password123
        mc mb myminio/acervo-mestre --ignore-existing
        mc anonymous set download myminio/acervo-mestre
    "
    echo "Bucket recriado com sucesso!"
}

run_migrations() {
    echo "Executando migrações do Alembic..."
    alembic upgrade head
    echo "Migrações concluídas!"
}

run_tests() {
    echo "Executando testes de recursos..."
    python scripts/test_recursos.py
}

clean_volumes() {
    echo "AVISO: Isso irá apagar TODOS os dados!"
    read -p "Tem certeza? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        docker-compose down -v
        rm -rf postgres_data/ minio_data/
        echo "Volumes limpos!"
    else
        echo "Operação cancelada."
    fi
}

install_deps() {
    echo "Instalando dependências Python..."
    pip install -r requirements.txt
    echo "Dependências instaladas!"
}

open_minio_console() {
    echo "Abrindo MinIO Console..."
    echo "URL: http://localhost:9001"
    echo "Usuário: admin"
    echo "Senha: password123"
    xdg-open http://localhost:9001 2>/dev/null || open http://localhost:9001 2>/dev/null || start http://localhost:9001
}

open_swagger() {
    echo "Abrindo Swagger UI..."
    echo "URL: http://localhost:8000/docs"
    xdg-open http://localhost:8000/docs 2>/dev/null || open http://localhost:8000/docs 2>/dev/null || start http://localhost:8000/docs
}

# Loop principal
while true; do
    show_menu
    read -p "Opção: " option
    
    case $option in
        1) start_services ;;
        2) stop_services ;;
        3) view_minio_logs ;;
        4) view_postgres_logs ;;
        5) recreate_bucket ;;
        6) run_migrations ;;
        7) run_tests ;;
        8) clean_volumes ;;
        9) install_deps ;;
        10) open_minio_console ;;
        11) open_swagger ;;
        0) echo "Saindo..."; exit 0 ;;
        *) echo "Opção inválida!" ;;
    esac
done
