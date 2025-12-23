import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Configurações da aplicação."""
    
    # --- Database ---
    DATABASE_URL: str 
    
    # --- JWT & Segurança ---
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # --- MinIO / S3 ---
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    S3_BUCKET_NAME: str
    S3_ENDPOINT_URL: str
    S3_REGION: str = "us-east-1"
    
    # --- Limites de upload ---
    MAX_FILE_SIZE_MB: int = 100
    ALLOWED_MIME_TYPES: list[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "video/mp4",
        "image/jpeg",
        "image/png",
        "image/gif",
    ]

    # --- Email (Mailtrap)
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str = "no-reply@acervomestre.com"
    MAIL_PORT: int = 2525
    MAIL_SERVER: str = "sandbox.smtp.mailtrap.io"

    # --- Frontend ---
    FRONTEND_URL: str = "http://localhost:3000"

    # Lê do arquivo .env
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()