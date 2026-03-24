import requests
import os

def test_import():
    url = "http://localhost:8000/api/calcular/importar-excel"
    file_path = os.path.join(os.path.dirname(__file__), "sample.xlsm")
    
    # Simular o upload
    with open(file_path, "rb") as f:
        files = {"file": f}
        try:
            response = requests.post(url, files=files)
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print("Importação Bem-sucedida!")
                print(f"Projeto: {data['cabecalho']['projeto']}")
                print(f"Ponto: {data['cabecalho']['ponto']}")
                print(f"Poste: {data['poste']['modelo_poste']}")
                # Verificar se mt1 tem dade
                if any(t['tipo_rede'] != "" for t in data['mt1']):
                    print("MT1: OK (Dados extraídos)")
                else:
                    print("MT1: FAILED (Sem dados)")
            else:
                print(f"Erro: {response.text}")
        except Exception as e:
            print(f"Erro na conexão: {e}")

if __name__ == "__main__":
    test_import()
