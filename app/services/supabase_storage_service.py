import uuid
import os
from supabase import create_client, Client
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings


class SupabaseStorageService:
    """Serviço para gerenciar uploads de arquivos no Supabase Storage."""
    
    def __init__(self):
        """Inicializa o cliente Supabase."""
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_KEY
        self.bucket = settings.SUPABASE_BUCKET_NAME
        self.supabase: Client = create_client(self.url, self.key)
    
    async def upload_file(self, file: UploadFile) -> dict:
        """
        Faz upload de um arquivo para o Supabase Storage.
        
        Args:
            file (UploadFile): Arquivo enviado via multipart/form-data
            
        Returns:
            dict: Dicionário com metadados do arquivo:
                - storage_key (str): Chave única do arquivo no bucket
                - public_url (str): URL pública do arquivo
                - mime_type (str): Tipo MIME do arquivo
                - tamanho_bytes (int): Tamanho do arquivo em bytes
                - filename (str): Nome original do arquivo
                
        Raises:
            HTTPException (400): Se o tipo de arquivo não for permitido
            HTTPException (413): Se o arquivo exceder o tamanho máximo
            HTTPException (500): Se ocorrer erro no upload
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
        
        # Gerar nome único para o arquivo (UUID)
        file_extension = file.filename.split(".")[-1] if "." in file.filename else ""
        storage_key = f"{uuid.uuid4()}.{file_extension}" if file_extension else str(uuid.uuid4())
        
        try:
            # Upload para o Supabase Storage
            self.supabase.storage.from_(self.bucket).upload(
                path=storage_key,
                file=content,
                file_options={"content-type": file.content_type}
            )
            
            # Gerar a URL pública
            public_url = self.supabase.storage.from_(self.bucket).get_public_url(storage_key)
            
            return {
                "storage_key": storage_key,
                "public_url": public_url,
                "mime_type": file.content_type,
                "tamanho_bytes": file_size,
                "filename": file.filename,
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao fazer upload do arquivo: {str(e)}"
            )
    
    async def delete_file(self, storage_key: str) -> bool:
        """
        Remove um arquivo do Supabase Storage.
        
        Args:
            storage_key (str): Chave do arquivo no bucket
            
        Returns:
            bool: True se removido com sucesso
            
        Raises:
            HTTPException (500): Se ocorrer erro na remoção
        """
        try:
            self.supabase.storage.from_(self.bucket).remove([storage_key])
            return True
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao remover o arquivo: {str(e)}"
            )
    
    def get_public_url(self, storage_key: str) -> str:
        """
        Obtém a URL pública de um arquivo.
        
        Args:
            storage_key (str): Chave do arquivo no bucket
            
        Returns:
            str: URL pública do arquivo
        """
        return self.supabase.storage.from_(self.bucket).get_public_url(storage_key)


# Instância global do serviço
supabase_storage_service = SupabaseStorageService()
