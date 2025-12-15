"""
Script de teste para o módulo de Recursos.
Execute após iniciar o servidor: uvicorn main:app --reload
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_criar_recurso_nota():
    """Testa criação de recurso do tipo NOTA."""
    print("\n=== Testando criação de NOTA ===")
    
    data = {
        "titulo": "Resumo de Matemática",
        "descricao": "Resumo sobre equações de segundo grau",
        "estrutura": "NOTA",
        "visibilidade": "PUBLICO",
        "conteudo_markdown": "# Equações de Segundo Grau\n\n## Fórmula de Bhaskara\n\nx = (-b ± √(b² - 4ac)) / 2a"
    }
    
    response = requests.post(f"{BASE_URL}/recursos/create", data=data)
    print(f"Status: {response.status_code}")
    print(f"Resposta: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.json().get("id")


def test_criar_recurso_url():
    """Testa criação de recurso do tipo URL."""
    print("\n=== Testando criação de URL ===")
    
    data = {
        "titulo": "Aula de Física no YouTube",
        "descricao": "Vídeo explicativo sobre cinemática",
        "estrutura": "URL",
        "visibilidade": "PUBLICO",
        "url_externa": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    }
    
    response = requests.post(f"{BASE_URL}/recursos/create", data=data)
    print(f"Status: {response.status_code}")
    print(f"Resposta: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.json().get("id")


def test_criar_recurso_upload():
    """Testa criação de recurso do tipo UPLOAD."""
    print("\n=== Testando criação de UPLOAD ===")
    print("NOTA: Para testar upload real, você precisa ter um arquivo PDF.")
    print("Exemplo comentado no código.")
    
    # Descomente e ajuste o caminho do arquivo para testar:
    # files = {
    #     "file": ("documento.pdf", open("caminho/para/seu/arquivo.pdf", "rb"), "application/pdf")
    # }
    # data = {
    #     "titulo": "Material de Apoio",
    #     "descricao": "PDF com exercícios",
    #     "estrutura": "UPLOAD",
    #     "visibilidade": "PUBLICO"
    # }
    # response = requests.post(f"{BASE_URL}/recursos/create", data=data, files=files)
    # print(f"Status: {response.status_code}")
    # print(f"Resposta: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    # return response.json().get("id")
    
    return None


def test_listar_recursos():
    """Testa listagem de recursos."""
    print("\n=== Testando listagem de recursos ===")
    
    response = requests.get(f"{BASE_URL}/recursos/get_all?page=1&per_page=10")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Total de recursos: {data.get('total')}")
    print(f"Página: {data.get('page')} de {data.get('total_pages')}")
    print(f"Recursos encontrados: {len(data.get('items', []))}")
    

def test_buscar_recurso(recurso_id):
    """Testa busca de um recurso específico."""
    if not recurso_id:
        return
    
    print(f"\n=== Testando busca do recurso {recurso_id} ===")
    
    response = requests.get(f"{BASE_URL}/recursos/get/{recurso_id}")
    print(f"Status: {response.status_code}")
    print(f"Resposta: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def test_download_recurso(recurso_id):
    """Testa download/acesso ao recurso."""
    if not recurso_id:
        return
    
    print(f"\n=== Testando download do recurso {recurso_id} ===")
    
    response = requests.post(f"{BASE_URL}/recursos/{recurso_id}/download")
    print(f"Status: {response.status_code}")
    print(f"Resposta: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def test_filtrar_recursos():
    """Testa filtros de busca."""
    print("\n=== Testando filtros ===")
    
    # Filtrar por palavra-chave
    print("\n-- Filtro por palavra-chave: 'Matemática' --")
    response = requests.get(f"{BASE_URL}/recursos/get_all?palavra_chave=Matemática")
    print(f"Recursos encontrados: {len(response.json().get('items', []))}")
    
    # Filtrar por estrutura
    print("\n-- Filtro por estrutura: 'NOTA' --")
    response = requests.get(f"{BASE_URL}/recursos/get_all?estrutura=NOTA")
    print(f"Recursos encontrados: {len(response.json().get('items', []))}")
    
    print("\n-- Filtro por estrutura: 'URL' --")
    response = requests.get(f"{BASE_URL}/recursos/get_all?estrutura=URL")
    print(f"Recursos encontrados: {len(response.json().get('items', []))}")


if __name__ == "__main__":
    print("=" * 60)
    print("TESTE DO MÓDULO DE RECURSOS - ACERVO MESTRE")
    print("=" * 60)
    print("\nCertifique-se de que:")
    print("1. O servidor está rodando (uvicorn main:app --reload)")
    print("2. O Docker está rodando (docker-compose up -d)")
    print("3. As migrações foram executadas (alembic upgrade head)")
    
    input("\nPressione ENTER para continuar...")
    
    try:
        # Criar recursos de teste
        nota_id = test_criar_recurso_nota()
        url_id = test_criar_recurso_url()
        test_criar_recurso_upload()
        
        # Listar recursos
        test_listar_recursos()
        
        # Buscar recursos específicos
        test_buscar_recurso(nota_id)
        test_buscar_recurso(url_id)
        
        # Testar download (para URL)
        test_download_recurso(url_id)
        
        # Testar filtros
        test_filtrar_recursos()
        
        print("\n" + "=" * 60)
        print("TESTES CONCLUÍDOS!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERRO: Não foi possível conectar ao servidor.")
        print("Certifique-se de que o servidor está rodando em http://localhost:8000")
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
