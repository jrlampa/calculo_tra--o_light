#!/usr/bin/env python3
"""Teste para validar que apenas o campo 'Projeto' é obrigatório."""

import sys
import os
from uuid import uuid4

# Add python directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.schemas import ProjetoIn
from models.projeto import ProjetoCreate


def test_campos_opcionais():
    """Testa que apenas o campo 'Projeto' é obrigatório."""
    print("=== Teste de Campos Opcionais ===")
    
    # Teste 1: Apenas campo obrigatório preenchido
    print("\n--- Teste 1: Apenas campo obrigatório preenchido ---")
    try:
        projeto_in = ProjetoIn(nome="Projeto Teste")
        print(f"✓ ProjetoIn válido: {projeto_in.dict()}")
        
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
        print("✓ Teste 1 passou: Apenas campo obrigatório preenchido")
        
    except Exception as e:
        print(f"✗ Teste 1 falhou: {e}")
    
    # Teste 2: Todos os campos preenchidos
    print("\n--- Teste 2: Todos os campos preenchidos ---")
    try:
        projeto_in = ProjetoIn(
            orgao="IM3 Brasil",
            ns="TESTE-123",
            nome="Projeto Completo",
            endereco="Endereço Teste",
            estudado_por="Teste User",
            matricula="12345",
            data_estudo="24/03/2026"
        )
        print(f"✓ ProjetoIn válido: {projeto_in.dict()}")
        
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
        print("✓ Teste 2 passou: Todos os campos preenchidos")
        
    except Exception as e:
        print(f"✗ Teste 2 falhou: {e}")
    
    # Teste 3: Campo obrigatório vazio (deve falhar)
    print("\n--- Teste 3: Campo obrigatório vazio (deve falhar) ---")
    try:
        projeto_in = ProjetoIn(nome="")
        print(f"✗ Teste 3 falhou: Deveria ter rejeitado nome vazio")
        
    except Exception as e:
        print(f"✓ Teste 3 passou: Corretamente rejeitou nome vazio: {e}")
    
    # Teste 4: Campo obrigatório ausente (deve falhar)
    print("\n--- Teste 4: Campo obrigatório ausente (deve falhar) ---")
    try:
        projeto_in = ProjetoIn()
        print(f"✗ Teste 4 falhou: Deveria ter rejeitado ausência de nome")
        
    except Exception as e:
        print(f"✓ Teste 4 passou: Corretamente rejeitou ausência de nome: {e}")
    
    # Teste 5: Dados com campos extras (deve ser rejeitado)
    print("\n--- Teste 5: Dados com campos extras (deve ser rejeitado) ---")
    try:
        projeto_in = ProjetoIn(
            orgao="IM3 Brasil",
            ns="TESTE-123",
            nome="Projeto Teste",
            endereco="Endereço Teste",
            estudado_por="Teste User",
            matricula="12345",
            data_estudo="24/03/2026",
            campo_extra="valor"  # Campo extra que deve ser rejeitado
        )
        print(f"✗ Teste 5 falhou: Deveria ter rejeitado campo extra")
        
    except Exception as e:
        print(f"✓ Teste 5 passou: Corretamente rejeitou campo extra: {e}")


def test_tipos_campos():
    """Testa os tipos e valores padrão dos campos."""
    print("\n=== Teste de Tipos e Valores Padrão ===")
    
    projeto_in = ProjetoIn(nome="Projeto Teste")
    
    print(f"orgao: '{projeto_in.orgao}' (tipo: {type(projeto_in.orgao)})")
    print(f"ns: '{projeto_in.ns}' (tipo: {type(projeto_in.ns)})")
    print(f"nome: '{projeto_in.nome}' (tipo: {type(projeto_in.nome)})")
    print(f"endereco: '{projeto_in.endereco}' (tipo: {type(projeto_in.endereco)})")
    print(f"estudado_por: '{projeto_in.estudado_por}' (tipo: {type(projeto_in.estudado_por)})")
    print(f"matricula: '{projeto_in.matricula}' (tipo: {type(projeto_in.matricula)})")
    print(f"data_estudo: '{projeto_in.data_estudo}' (tipo: {type(projeto_in.data_estudo)})")
    
    # Verificar valores padrão
    assert projeto_in.orgao == "", f"orgao deveria ser vazio, mas é '{projeto_in.orgao}'"
    assert projeto_in.ns == "", f"ns deveria ser vazio, mas é '{projeto_in.ns}'"
    assert projeto_in.endereco == "", f"endereco deveria ser vazio, mas é '{projeto_in.endereco}'"
    assert projeto_in.estudado_por == "", f"estudado_por deveria ser vazio, mas é '{projeto_in.estudado_por}'"
    assert projeto_in.matricula == "", f"matricula deveria ser vazia, mas é '{projeto_in.matricula}'"
    
    print("✓ Teste de tipos e valores padrão passou")


if __name__ == "__main__":
    test_campos_opcionais()
    test_tipos_campos()
    print("\n=== Testes concluídos ===")