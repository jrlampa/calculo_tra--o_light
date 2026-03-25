#!/usr/bin/env python3
"""Teste de validação de schema para identificar problemas de tipagem."""

import sys
import os
from uuid import uuid4

# Add python directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.schemas import ProjetoIn
from models.projeto import ProjetoCreate


def test_schema_validation():
    """Testa a validação do schema ProjetoIn."""
    print("=== Teste de Validação de Schema ===")
    
    # Dados de teste que causam problemas
    test_cases = [
        {
            "name": "Caso Normal",
            "data": {
                "orgao": "IM3 Brasil",
                "ns": "TESTE-123",
                "nome": "Projeto de Teste",
                "endereco": "Endereço Teste",
                "estudado_por": "Teste User",
                "matricula": "12345",
                "data_estudo": "24/03/2026"
            }
        },
        {
            "name": "Caso com total_pontos string",
            "data": {
                "orgao": "IM3 Brasil",
                "ns": "TESTE-123",
                "nome": "Projeto de Teste",
                "endereco": "Endereço Teste",
                "estudado_por": "Teste User",
                "matricula": "12345",
                "data_estudo": "24/03/2026",
                "total_pontos": "0"  # String ao invés de número
            }
        },
        {
            "name": "Caso com campos ausentes",
            "data": {
                "orgao": "IM3 Brasil",
                "ns": "TESTE-123",
                "nome": "Projeto de Teste",
                "endereco": "Endereço Teste",
                "estudado_por": "Teste User",
                "matricula": "12345",
                "data_estudo": "24/03/2026",
                "created_at": "2026-03-24T20:00:00",  # Campo que não deveria estar aqui
                "updated_at": "2026-03-24T20:00:00",  # Campo que não deveria estar aqui
            }
        },
        {
            "name": "Caso com data futura",
            "data": {
                "orgao": "IM3 Brasil",
                "ns": "TESTE-123",
                "nome": "Projeto de Teste",
                "endereco": "Endereço Teste",
                "estudado_por": "Teste User",
                "matricula": "12345",
                "data_estudo": "24/03/2027"  # Data futura
            }
        },
        {
            "name": "Caso com matricula vazia",
            "data": {
                "orgao": "IM3 Brasil",
                "ns": "TESTE-123",
                "nome": "Projeto de Teste",
                "endereco": "Endereço Teste",
                "estudado_por": "Teste User",
                "matricula": "",  # Matricula vazia
                "data_estudo": "24/03/2026"
            }
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
            
        except Exception as e:
            print(f"✗ Erro: {e}")
            print(f"  Dados: {test_case['data']}")


def test_field_types():
    """Testa os tipos dos campos."""
    print("\n=== Teste de Tipos de Campos ===")
    
    projeto_in = ProjetoIn(
        orgao="IM3 Brasil",
        ns="TESTE-123",
        nome="Projeto de Teste",
        endereco="Endereço Teste",
        estudado_por="Teste User",
        matricula="12345",
        data_estudo="24/03/2026"
    )
    
    print(f"orgao: {type(projeto_in.orgao)} = {projeto_in.orgao}")
    print(f"ns: {type(projeto_in.ns)} = {projeto_in.ns}")
    print(f"nome: {type(projeto_in.nome)} = {projeto_in.nome}")
    print(f"endereco: {type(projeto_in.endereco)} = {projeto_in.endereco}")
    print(f"estudado_por: {type(projeto_in.estudado_por)} = {projeto_in.estudado_por}")
    print(f"matricula: {type(projeto_in.matricula)} = {projeto_in.matricula}")
    print(f"data_estudo: {type(projeto_in.data_estudo)} = {projeto_in.data_estudo}")


if __name__ == "__main__":
    test_schema_validation()
    test_field_types()