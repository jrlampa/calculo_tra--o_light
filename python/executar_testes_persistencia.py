#!/usr/bin/env python3
"""Script para executar todos os testes de persistência implementados."""

import subprocess
import sys
import os
from pathlib import Path

def executar_teste(teste_path, descricao):
    """Executa um teste específico e retorna o resultado."""
    print(f"\n{'='*60}")
    print(f"Executando: {descricao}")
    print(f"Arquivo: {teste_path}")
    print(f"{'='*60}")
    
    try:
        # Mudar para o diretório do Python
        os.chdir('python')
        
        # Executar o teste
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            str(teste_path), 
            '-v', '--tb=short'
        ], capture_output=True, text=True, timeout=120)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {descricao} - SUCESSO")
            return True
        else:
            print(f"❌ {descricao} - FALHA (código: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {descricao} - TIMEOUT (mais de 120s)")
        return False
    except Exception as e:
        print(f"💥 {descricao} - ERRO: {e}")
        return False
    finally:
        # Voltar ao diretório raiz
        os.chdir('..')

def main():
    """Executa todos os testes de persistência."""
    print("🚀 Iniciando execução dos testes de persistência...")
    
    # Definir os testes a serem executados
    testes = [
        ("tests/test_hierarquia_completa.py", "Testes de Hierarquia Completa"),
        ("tests/test_persistencia_calculo.py", "Testes de Persistência de Cálculos"),
        ("tests/test_parity_excel.py", "Testes de Parity Excel"),
        ("tests/test_integracao_real.py", "Testes de Integração Real"),
    ]
    
    resultados = []
    
    # Executar cada teste
    for teste_path, descricao in testes:
        sucesso = executar_teste(teste_path, descricao)
        resultados.append((descricao, sucesso))
    
    # Resumo final
    print(f"\n{'='*60}")
    print("RESUMO DA EXECUÇÃO DOS TESTES")
    print(f"{'='*60}")
    
    total_testes = len(resultados)
    testes_sucesso = sum(1 for _, sucesso in resultados if sucesso)
    testes_falha = total_testes - testes_sucesso
    
    for descricao, sucesso in resultados:
        status = "✅ SUCESSO" if sucesso else "❌ FALHA"
        print(f"{status} - {descricao}")
    
    print(f"\n{'='*60}")
    print(f"Total de testes: {total_testes}")
    print(f"Testes com sucesso: {testes_sucesso}")
    print(f"Testes com falha: {testes_falha}")
    print(f"Taxa de sucesso: {(testes_sucesso/total_testes)*100:.1f}%")
    print(f"{'='*60}")
    
    # Retornar código de saída
    if testes_falha == 0:
        print("🎉 Todos os testes foram executados com sucesso!")
        return 0
    else:
        print("⚠️  Alguns testes falharam. Verifique os logs acima.")
        return 1

if __name__ == "__main__":
    sys.exit(main())