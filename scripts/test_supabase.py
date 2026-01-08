"""
Script para testar a conexão com o Supabase Storage.
Execute: python scripts/test_supabase.py
"""
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings
from supabase import create_client

def test_supabase_connection():
    """Testa a conexão com o Supabase."""
    print("🔍 Testando conexão com Supabase...\n")
    
    # Verificar credenciais
    print(f"📋 Configurações:")
    print(f"   SUPABASE_URL: {settings.SUPABASE_URL}")
    print(f"   SUPABASE_KEY: {'*' * 20}...")
    print(f"   SUPABASE_BUCKET: {settings.SUPABASE_BUCKET_NAME}\n")
    
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        print("❌ Erro: SUPABASE_URL ou SUPABASE_KEY não configurados no .env")
        return False
    
    try:
        # Criar cliente
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        print("✅ Cliente Supabase criado com sucesso!\n")
        
        # Testar acesso ao bucket
        print(f"🪣 Testando acesso ao bucket '{settings.SUPABASE_BUCKET_NAME}'...")
        buckets = supabase.storage.list_buckets()
        
        bucket_names = [bucket.name for bucket in buckets]
        print(f"   Buckets disponíveis: {bucket_names}")
        
        if settings.SUPABASE_BUCKET_NAME in bucket_names:
            print(f"   ✅ Bucket '{settings.SUPABASE_BUCKET_NAME}' encontrado!\n")
        else:
            print(f"   ⚠️ Bucket '{settings.SUPABASE_BUCKET_NAME}' não encontrado.")
            print(f"   💡 Crie o bucket no dashboard do Supabase.\n")
            return False
        
        print("🎉 Conexão com Supabase Storage OK!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao conectar com Supabase: {e}")
        return False

if __name__ == "__main__":
    success = test_supabase_connection()
    sys.exit(0 if success else 1)
