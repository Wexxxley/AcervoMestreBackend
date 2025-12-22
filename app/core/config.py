import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Configurações da aplicação carregadas de variáveis de ambiente."""
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user_acervo:senha_segura@localhost:5432/acervo_mestre_db"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # MinIO / S3
    AWS_ACCESS_KEY_ID: str = "admin"
    AWS_SECRET_ACCESS_KEY: str = "password123"
    S3_BUCKET_NAME: str = "acervo-mestre"
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_REGION: str = "us-east-1"  # MinIO aceita qualquer região
    
    # Limites de upload
    MAX_FILE_SIZE_MB: int = 100  # Tamanho máximo de arquivo em MB
    ALLOWED_MIME_TYPES: list[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # DOCX
        "application/msword",  # DOC
        "video/mp4",
        "image/jpeg",
        "image/png",
        "image/gif",
    ]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# Instância global das configurações
settings = Settings()
