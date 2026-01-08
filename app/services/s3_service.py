import boto3
import uuid
from typing import BinaryIO, Optional
from fastapi import UploadFile, HTTPException, status
from botocore.exceptions import ClientError
from app.core.config import settings

class S3Service:
    """Service para gerenciar uploads e downloads de arquivos no MinIO/S3."""
    
    def __init__(self):
        """Inicializa o cliente boto3 para MinIO/S3."""
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.S3_REGION,
        )
        self.bucket_name = settings.S3_BUCKET_NAME
    
    async def upload_file(self, file: UploadFile) -> dict:
        """
        Faz upload de um arquivo para o MinIO/S3.
        """
        # Validar tipo de arquivo
        if file.content_type not in settings.ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de arquivo não permitido. Tipos aceitos: {', '.join(settings.ALLOWED_MIME_TYPES)}"
            )
        
        # Ler o arquivo para verificar o tamanho
        content = await file.read()
        file_size = len(content)
        
        # Validar tamanho
        max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Arquivo muito grande. Tamanho máximo: {settings.MAX_FILE_SIZE_MB}MB"
            )
        
        # Gerar nome único para o arquivo
        file_extension = file.filename.split(".")[-1] if "." in file.filename else ""
        storage_key = f"{uuid.uuid4()}.{file_extension}" if file_extension else str(uuid.uuid4())
        
        try:
            # Upload do arquivo para o MinIO/S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=storage_key,
                Body=content,
                ContentType=file.content_type,
                # Dica: Adicionar ContentDisposition no upload ajuda se acessar o link direto
                # Mas vamos controlar isso dinamicamente no get_file_url
            )
            
            return {
                "storage_key": storage_key,
                "mime_type": file.content_type,
                "tamanho_bytes": file_size,
                "filename": file.filename,
            }
            
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao fazer upload do arquivo: {str(e)}"
            )
    
    async def delete_file(self, storage_key: str) -> bool:
        """
        Remove um arquivo do MinIO/S3.
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=storage_key
            )
            return True
            
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao deletar arquivo: {str(e)}"
            )
    
    def get_file_url(self, storage_key: str, expiration: int = 3600, download: bool = True) -> Optional[str]:
        """
        Gera uma URL assinada (Presigned URL) para acesso ao arquivo.
        
        Args:
            storage_key (str): Chave do arquivo no bucket
            expiration (int): Tempo de expiração do link em segundos (Padrão: 1 hora)
            download (bool): 
                - Se True: Força o download (attachment).
                - Se False: Tenta abrir no navegador (inline).
            
        Returns:
            str: URL assinada temporária ou None em caso de erro.
        """
        try:
            # Define o comportamento do navegador
            disposition = 'attachment' if download else 'inline'
            
            response = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': storage_key,
                    'ResponseContentDisposition': disposition,
                    # Opcional: Forçar o Content-Type ajuda o navegador a entender o arquivo
                    # 'ResponseContentType': 'application/pdf' 
                },
                ExpiresIn=expiration
            )
            return response
        except ClientError as e:
            print(f"Erro ao gerar URL assinada: {e}")
            return None

# Instância global do serviço
s3_service = S3Service()