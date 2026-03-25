#!/usr/bin/env python3
"""Teste de depuração para identificar o problema de persistência de projetos."""

import asyncio
import sys
import os
from uuid import uuid4

# Add python directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.schemas import ProjetoIn
from services.projeto_service import ProjetoService
from repositories.projeto_repository import ProjetoRepository
from models.projeto import ProjetoCreate
from db.pool import db_pool


async def test_persistencia_direta():
    """Teste de persistência direta no repositório."""
    print("=== Teste de Persistência Direta ===")
    
    # Criar dados de teste
    projeto_in = ProjetoIn(
        orgao="IM3 Brasil",
        ns="TESTE-123",
        nome="Projeto de Teste",
        endereco="Endereço Teste",
        estudado_por="Teste User",
        matricula="12345",
        data_estudo="24/03/2026"
    )
    
    user_id = uuid4()
    
    try:
        # Criar serviço
        projeto_repository = ProjetoRepository(db_pool)
        projeto_service = ProjetoService(projeto_repository)
        
        print(f"1. Dados de entrada: {projeto_in.dict()}")
        print(f"2. User ID: {user_id}")
        
        # Testar criação direta
        projeto_create = ProjetoCreate(
            orgao=projeto_in.orgao,
            ns=projeto_in.ns,
            nome=projeto_in.nome,
            endereco=projeto_in.endereco,
            estudado_por=projeto_in.estudado_por,
            matricula=projeto_in.matricula,
            data_estudo=projeto_in.data_estudo,
            owner_id=user_id,
        )
        
        print(f"3. ProjetoCreate: {projeto_create.dict()}")
        
        # Testar criação
        projeto = await projeto_service.create_projeto(projeto_create, user_id)
        
        print(f"4. Projeto criado: {projeto.dict()}")
        print(f"5. ID do projeto: {projeto.id}")
        
        # Verificar se o projeto foi realmente salvo
        projeto_salvo = await projeto_service.get_projeto(projeto.id, user_id)
        print(f"6. Projeto recuperado: {projeto_salvo.dict()}")
        
        return True
        
    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_conexao_banco():
    """Teste de conexão com o banco de dados."""
    print("\n=== Teste de Conexão com Banco ===")
    
    try:
        # Testar conexão
        result = await db_pool.fetch_one("SELECT NOW() as timestamp")
        print(f"Conexão bem-sucedida: {result}")
        return True
    except Exception as e:
        print(f"Erro de conexão: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_schema_validation():
    """Teste de validação de schema."""
    print("\n=== Teste de Validação de Schema ===")
    
    try:
        # Testar validação do schema
        projeto_in = ProjetoIn(
            orgao="IM3 Brasil",
            ns="TESTE-123",
            nome="Projeto de Teste",
            endereco="Endereço Teste",
            estudado_por="Teste User",
            matricula="12345",
            data_estudo="24/03/2026"
        )
        
        print(f"Schema válido: {projeto_in.dict()}")
        return True
        
    except Exception as e:
        print(f"Erro de validação: {e}")
        return False


async def main():
    """Executa todos os testes de depuração."""
    print("Iniciando testes de depuração de persistência...\n")
    
    # Testar conexão
    conexao_ok = await test_conexao_banco()
    
    # Testar validação
    schema_ok = await test_schema_validation()
    
    # Testar persistência
    persistencia_ok = await test_persistencia_direta()
    
    print(f"\n=== Resultados ===")
    print(f"Conexão com banco: {'✓' if conexao_ok else '✗'}")
    print(f"Validação de schema: {'✓' if schema_ok else '✗'}")
    print(f"Persistência: {'✓' if persistencia_ok else '✗'}")
    
    if conexao_ok and schema_ok and persistencia_ok:
        print("Todos os testes passaram!")
    else:
        print("Alguns testes falharam. Verifique os erros acima.")


if __name__ == "__main__":
    asyncio.run(main())