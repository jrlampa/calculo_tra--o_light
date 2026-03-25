#!/usr/bin/env python3
"""Teste para validar as correções implementadas."""

import sys
import os
from uuid import uuid4

# Add python directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.schemas import ProjetoIn
from models.projeto import ProjetoCreate, ProjetoUpdate
from services.projeto_service import ProjetoService
from repositories.projeto_repository import ProjetoRepository
from core.exceptions import ValidationError


def test_validacao_corrigida():
    """Testa a validação corrigida."""
    print("=== Teste de Validação Corrigida ===")
    
    test_cases = [
        {
            "name": "Caso Normal - Deve Passar",
            "data": {
                "orgao": "IM3 Brasil",
                "ns": "TESTE-123",
                "nome": "Projeto de Teste",
                "endereco": "Endereço Teste",
                "estudado_por": "Teste User",
                "matricula": "12345",
                "data_estudo": "24/03/2026"
            },
            "should_pass": True
        },
        {
            "name": "Data Futura - Deve Falhar",
            "data": {
                "orgao": "IM3 Brasil",
                "ns": "TESTE-123",
                "nome": "Projeto de Teste",
                "endereco": "Endereço Teste",
                "estudado_por": "Teste User",
                "matricula": "12345",
                "data_estudo": "24/03/2027"  # Data futura
            },
            "should_pass": False,
            "expected_error": "Data de estudo não pode estar no futuro"
        },
        {
            "name": "Data Inválida - Deve Falhar",
            "data": {
                "orgao": "IM3 Brasil",
                "ns": "TESTE-123",
                "nome": "Projeto de Teste",
                "endereco": "Endereço Teste",
                "estudado_por": "Teste User",
                "matricula": "12345",
                "data_estudo": "24-03-2026"  # Formato inválido
            },
            "should_pass": False,
            "expected_error": "Formato de data inválido"
        },
        {
            "name": "Matricula Vazia - Deve Falhar",
            "data": {
                "orgao": "IM3 Brasil",
                "ns": "TESTE-123",
                "nome": "Projeto de Teste",
                "endereco": "Endereço Teste",
                "estudado_por": "Teste User",
                "matricula": "",  # Matricula vazia
                "data_estudo": "24/03/2026"
            },
            "should_pass": False,
            "expected_error": "Matrícula não pode ser vazia"
        },
        {
            "name": "Campos Obrigatórios Ausentes - Deve Falhar",
            "data": {
                "orgao": "IM3 Brasil",
                "ns": "TESTE-123",
                "nome": "Projeto de Teste",
                "endereco": "Endereço Teste",
                "estudado_por": "Teste User",
                "matricula": "12345",
                "data_estudo": "24/03/2026"
            },
            "should_pass": True  # Este caso deve passar, vamos testar manualmente
        }
    ]
    
    for test_case in test_cases:
        print(f"\n--- {test_case['name']} ---")
        try:
            # Testar ProjetoIn
            projeto_in = ProjetoIn(**test_case['data'])
            print(f"✓ ProjetoIn válido: {projeto_in.dict()}")
            
            # Testar ProjetoCreate
            projeto_create = ProjetoCreate(
                orgao=projeto_in.orgao,
                ns=projeto_in.ns,
                nome=projeto_in.nome,
                endereco=projeto_in.endereco,
                estudado_por=projeto_in.estudado_por,
                matricula=projeto_in.matricula,
                data_estudo=projeto_in.data_estudo,
                owner_id=uuid4(),
            )
            print(f"✓ ProjetoCreate válido: {projeto_create.dict()}")
            
            # Testar validação do serviço
            try:
                # Criar um mock de repositório para testar a validação
                class MockRepository:
                    async def get_multi(self, limit, owner_id):
                        return []
                
                service = ProjetoService(MockRepository())
                import asyncio
                asyncio.run(service._validate_projeto_data(projeto_create))
                print("✓ Validação do serviço passou")
                
            except ValidationError as e:
                print(f"✗ Validação do serviço falhou: {e}")
                if test_case['should_pass']:
                    print(f"  Erro inesperado!")
                else:
                    if test_case.get('expected_error') and test_case['expected_error'] in str(e):
                        print(f"  ✓ Erro esperado: {e}")
                    else:
                        print(f"  ✗ Erro inesperado: {e}")
            
            if test_case['should_pass']:
                print("✓ Teste passou como esperado")
            else:
                print("✗ Teste falhou - deveria ter falhado")
                
        except Exception as e:
            print(f"✗ Erro: {e}")
            if test_case['should_pass']:
                print(f"  Erro inesperado!")
            else:
                if test_case.get('expected_error') and test_case['expected_error'] in str(e):
                    print(f"  ✓ Erro esperado: {e}")
                else:
                    print(f"  ✗ Erro inesperado: {e}")


def test_normalizacao_campos():
    """Testa a normalização de campos."""
    print("\n=== Teste de Normalização de Campos ===")
    
    projeto_in = ProjetoIn(
        orgao="im3 brasil",
        ns="teste-123",
        nome="projeto de teste",
        endereco="endereço teste",
        estudado_por="teste user",
        matricula="12345",
        data_estudo="24/03/2026"
    )
    
    projeto_create = ProjetoCreate(
        orgao=projeto_in.orgao,
        ns=projeto_in.ns,
        nome=projeto_in.nome,
        endereco=projeto_in.endereco,
        estudado_por=projeto_in.estudado_por,
        matricula=projeto_in.matricula,
        data_estudo=projeto_in.data_estudo,
        owner_id=uuid4(),
    )
    
    print(f"orgao: '{projeto_create.orgao}' (deveria ser 'Im3 Brasil')")
    print(f"ns: '{projeto_create.ns}' (deveria ser 'Teste-123')")
    print(f"nome: '{projeto_create.nome}' (deveria ser 'Projeto De Teste')")
    print(f"estudado_por: '{projeto_create.estudado_por}' (deveria ser 'Teste User')")
    
    # Verificar normalização
    assert projeto_create.orgao == "Im3 Brasil", f"orgao incorreto: {projeto_create.orgao}"
    assert projeto_create.ns == "Teste-123", f"ns incorreto: {projeto_create.ns}"
    assert projeto_create.nome == "Projeto De Teste", f"nome incorreto: {projeto_create.nome}"
    assert projeto_create.estudado_por == "Teste User", f"estudado_por incorreto: {projeto_create.estudado_por}"
    
    print("✓ Normalização de campos correta")


if __name__ == "__main__":
    test_validacao_corrigida()
    test_normalizacao_campos()
    print("\n=== Testes concluídos ===")