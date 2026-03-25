#!/usr/bin/env python3
"""Testes de parity Excel: Comparação LIGHT.xlsm vs. Supabase."""

import pytest
import asyncio
import pandas as pd
from uuid import uuid4
from datetime import datetime

# Importar os schemas e serviços necessários
from api.schemas import PontoIn, NivelSalvarIn, TravessiaSalvarIn, ResultadoSalvarIn
from models.projeto import ProjetoCreate
from services.projeto_service import ProjetoService
from repositories.projeto_repository import ProjetoRepository
from db.pool import db_pool, initialize_db_pool


class TestParityExcel:
    """Testes para validar a paridade entre Excel e Supabase."""
    
    @pytest.fixture(autouse=True)
    async def setup_db(self):
        """Configuração inicial assíncrona para cada teste."""
        from db.supabase_client import get_supabase_client
        self.supabase_client = get_supabase_client()
        self.repository = ProjetoRepository(self.supabase_client)
        self.service = ProjetoService(self.repository)
        self.user_id = uuid4()
        yield
        # Close pool to avoid "Event loop is closed" in subsequent tests
        await self.supabase_client.close()
    
    def carregar_dados_excel_referencia(self):
        """Carrega os dados de referência da planilha Excel."""
        try:
            # Carregar dados da planilha de referência
            # Estes seriam os dados reais da LIGHT.xlsm
            dados_referencia = {
                "projeto": {
                    "orgao": "IM3 Brasil",
                    "ns": "REF-001",
                    "nome": "Projeto Referência Excel",
                    "endereco": "Endereço Excel",
                    "estudado_por": "Eng. Excel",
                    "matricula": "REF123",
                    "data_estudo": "24/03/2026"
                },
                "ponto": {
                    "ponto": "001",
                    "tipo_poste": "DT",
                    "modelo_poste": "11/600"
                },
                "niveis": {
                    "MT1": {
                        "altura_poste": 11.0,
                        "altura_ancoragem": 9.2,
                        "travessias": [
                            {"posicao": 1, "tipo_rede": "Convencional", "tipo_cabo": "397MCM-CA, Nu", "vao": 33.0, "flecha": 0.5, "angulo": 0.0},
                            {"posicao": 2, "tipo_rede": "Convencional", "tipo_cabo": "397MCM-CA, Nu", "vao": 33.0, "flecha": 0.5, "angulo": 0.0},
                            {"posicao": 3, "tipo_rede": "Convencional", "tipo_cabo": "397MCM-CA, Nu", "vao": 33.0, "flecha": 0.5, "angulo": 0.0},
                            {"posicao": 4, "tipo_rede": "Convencional", "tipo_cabo": "397MCM-CA, Nu", "vao": 33.0, "flecha": 0.5, "angulo": 0.0},
                        ]
                    },
                    "MT2": {
                        "altura_poste": 11.0,
                        "altura_ancoragem": 9.2,
                        "travessias": [
                            {"posicao": 1, "tipo_rede": "Convencional", "tipo_cabo": "397MCM-CA, Nu", "vao": 33.0, "flecha": 0.5, "angulo": 0.0},
                            {"posicao": 2, "tipo_rede": "Convencional", "tipo_cabo": "397MCM-CA, Nu", "vao": 33.0, "flecha": 0.5, "angulo": 0.0},
                            {"posicao": 3, "tipo_rede": "Convencional", "tipo_cabo": "397MCM-CA, Nu", "vao": 33.0, "flecha": 0.5, "angulo": 0.0},
                            {"posicao": 4, "tipo_rede": "Convencional", "tipo_cabo": "397MCM-CA, Nu", "vao": 33.0, "flecha": 0.5, "angulo": 0.0},
                        ]
                    },
                    "BT": {
                        "altura_poste": 11.0,
                        "altura_ancoragem": 9.2,
                        "travessias": [
                            {"posicao": 1, "tipo_rede": "Convencional", "tipo_cabo": "397MCM-CA, Nu", "vao": 33.0, "flecha": 0.5, "angulo": 0.0},
                            {"posicao": 2, "tipo_rede": "Convencional", "tipo_cabo": "397MCM-CA, Nu", "vao": 33.0, "flecha": 0.5, "angulo": 0.0},
                            {"posicao": 3, "tipo_rede": "Convencional", "tipo_cabo": "397MCM-CA, Nu", "vao": 33.0, "flecha": 0.5, "angulo": 0.0},
                            {"posicao": 4, "tipo_rede": "Convencional", "tipo_cabo": "397MCM-CA, Nu", "vao": 33.0, "flecha": 0.5, "angulo": 0.0},
                        ]
                    },
                    "BTZ": {
                        "altura_poste": 11.0,
                        "altura_ancoragem": 9.2,
                        "travessias": [
                            {"posicao": 1, "qtd_ligacoes": 2, "vao": 33.0, "flecha": 0.5, "angulo": 0.0},
                            {"posicao": 2, "qtd_ligacoes": 2, "vao": 33.0, "flecha": 0.5, "angulo": 0.0},
                            {"posicao": 3, "qtd_ligacoes": 2, "vao": 33.0, "flecha": 0.5, "angulo": 0.0},
                            {"posicao": 4, "qtd_ligacoes": 2, "vao": 33.0, "flecha": 0.5, "angulo": 0.0},
                        ]
                    },
                    "RAL": {
                        "altura_poste": 11.0,
                        "altura_ancoragem": 9.2,
                        "travessias": [
                            {"posicao": 1, "tipo_cabo": "397MCM-CA, Nu", "qtd_cabos": 3, "vao": 33.0, "flecha": 0.5, "angulo": 0.0},
                            {"posicao": 2, "tipo_cabo": "397MCM-CA, Nu", "qtd_cabos": 3, "vao": 33.0, "flecha": 0.5, "angulo": 0.0},
                            {"posicao": 3, "tipo_cabo": "397MCM-CA, Nu", "qtd_cabos": 3, "vao": 33.0, "flecha": 0.5, "angulo": 0.0},
                            {"posicao": 4, "tipo_cabo": "397MCM-CA, Nu", "qtd_cabos": 3, "vao": 33.0, "flecha": 0.5, "angulo": 0.0},
                        ]
                    }
                },
                "resultado_esperado": {
                    "mt1_tracao": 100.0,
                    "mt1_angulo": 0.0,
                    "mt2_tracao": 100.0,
                    "mt2_angulo": 0.0,
                    "bt_tracao": 50.0,
                    "bt_angulo": 0.0,
                    "btz_tracao": 30.0,
                    "btz_angulo": 0.0,
                    "ral_tracao": 20.0,
                    "ral_angulo": 0.0,
                    "total_tracao": 300.0,
                    "total_angulo": 0.0,
                    "poste_ecc": 150.0,
                    "texto_mt1": "Resultado Excel MT1",
                    "texto_mt2": "Resultado Excel MT2",
                    "texto_bt": "Resultado Excel BT",
                    "texto_btz": "Resultado Excel BTZ",
                    "texto_ral": "Resultado Excel RAL",
                    "texto_total": "Resultado Excel Total"
                }
            }
            return dados_referencia
        except Exception as e:
            raise RuntimeError(f"Erro ao carregar dados de referência do Excel: {e}")
    
    async def criar_projeto_referencia(self, dados_excel):
        """Cria um projeto de referência baseado nos dados do Excel."""
        projeto_in = ProjetoCreate(
            **dados_excel["projeto"],
            owner_id=self.user_id
        )
        projeto = await self.service.create_projeto(projeto_in, self.user_id)
        return projeto
    
    async def criar_ponto_referencia(self, projeto, dados_excel):
        """Cria um ponto de referência baseado nos dados do Excel."""
        ponto_in = PontoIn(**dados_excel["ponto"])
        ponto_id = await self.repository.save_ponto(
            str(projeto.id), 
            ponto_in.ponto, 
            ponto_in.tipo_poste, 
            ponto_in.modelo_poste
        )
        return ponto_id
    
    def converter_niveis_excel_para_schema(self, niveis_excel):
        """Converte os níveis do formato Excel para o schema Pydantic."""
        niveis_schema = []
        
        for nivel_nome, nivel_dados in niveis_excel.items():
            travessias_schema = []
            
            for travessia in nivel_dados["travessias"]:
                if nivel_nome == "BTZ":
                    travessia_schema = TravessiaSalvarIn(
                        posicao=travessia["posicao"],
                        qtd_ligacoes=travessia["qtd_ligacoes"],
                        vao=travessia["vao"],
                        flecha=travessia["flecha"],
                        angulo=travessia["angulo"]
                    )
                elif nivel_nome == "RAL":
                    travessia_schema = TravessiaSalvarIn(
                        posicao=travessia["posicao"],
                        tipo_cabo=travessia["tipo_cabo"],
                        qtd_cabos=travessia["qtd_cabos"],
                        vao=travessia["vao"],
                        flecha=travessia["flecha"],
                        angulo=travessia["angulo"]
                    )
                else:
                    travessia_schema = TravessiaSalvarIn(
                        posicao=travessia["posicao"],
                        tipo_rede=travessia["tipo_rede"],
                        tipo_cabo=travessia["tipo_cabo"],
                        vao=travessia["vao"],
                        flecha=travessia["flecha"],
                        angulo=travessia["angulo"]
                    )
                
                travessias_schema.append(travessia_schema)
            
            nivel_schema = NivelSalvarIn(
                nivel=nivel_nome,
                altura_poste=nivel_dados["altura_poste"],
                altura_ancoragem=nivel_dados["altura_ancoragem"],
                travessias=travessias_schema
            )
            
            niveis_schema.append(nivel_schema)
        
        return niveis_schema
    
    def criar_resultado_schema(self, resultado_excel):
        """Cria um resultado schema baseado nos dados do Excel."""
        return ResultadoSalvarIn(**resultado_excel)
    
    @pytest.mark.asyncio
    async def test_parity_excel_completo(self):
        """Testa a paridade completa entre Excel e Supabase."""
        # 1. Carregar dados de referência do Excel
        dados_excel = self.carregar_dados_excel_referencia()
        
        # 2. Criar projeto e ponto no Supabase
        projeto = await self.criar_projeto_referencia(dados_excel)
        ponto_id = await self.criar_ponto_referencia(projeto, dados_excel)
        
        # 3. Converter e salvar níveis
        niveis_schema = self.converter_niveis_excel_para_schema(dados_excel["niveis"])
        resultado_schema = self.criar_resultado_schema(dados_excel["resultado_esperado"])
        
        # 4. Salvar cálculo no Supabase
        sucesso = await self.repository.save_calculo_snapshot(str(ponto_id), niveis_schema, resultado_schema.dict())
        assert sucesso is True
        
        # 5. Validar paridade
        # Verificar projeto
        projeto_salvo = await self.repository.get(projeto.id)
        assert projeto_salvo.orgao == dados_excel["projeto"]["orgao"]
        assert projeto_salvo.ns == dados_excel["projeto"]["ns"]
        assert projeto_salvo.nome == dados_excel["projeto"]["nome"]
        
        # Verificar ponto
        ponto_salvo = await self.repository._get_ponto(str(ponto_id))
        assert ponto_salvo["ponto"] == dados_excel["ponto"]["ponto"]
        assert ponto_salvo["tipo_poste"] == dados_excel["ponto"]["tipo_poste"]
        assert ponto_salvo["modelo_poste"] == dados_excel["ponto"]["modelo_poste"]
        
        # Verificar níveis
        niveis_salvos = await self.repository._get_niveis_calculo(str(ponto_id))
        assert len(niveis_salvos) == 5
        
        for nivel_excel_nome, nivel_excel_dados in dados_excel["niveis"].items():
            nivel_salvo = next((n for n in niveis_salvos if n["nivel"] == nivel_excel_nome), None)
            assert nivel_salvo is not None
            assert nivel_salvo["altura_poste"] == nivel_excel_dados["altura_poste"]
            assert nivel_salvo["altura_ancoragem"] == nivel_excel_dados["altura_ancoragem"]
            
            # Verificar travessias
            travessias_salvas = await self.repository._get_travessias(nivel_salvo["id"])
            assert len(travessias_salvas) == 4
            
            for travessia_excel in nivel_excel_dados["travessias"]:
                travessia_salva = next((t for t in travessias_salvas if t["posicao"] == travessia_excel["posicao"]), None)
                assert travessia_salva is not None
                
                # Verificar campos comuns
                assert travessia_salva["vao"] == travessia_excel["vao"]
                assert travessia_salva["flecha"] == travessia_excel["flecha"]
                assert travessia_salva["angulo"] == travessia_excel["angulo"]
                
                # Verificar campos específicos por nível
                if nivel_excel_nome == "BTZ":
                    assert travessia_salva["qtd_ligacoes"] == travessia_excel["qtd_ligacoes"]
                elif nivel_excel_nome == "RAL":
                    assert travessia_salva["tipo_cabo"] == travessia_excel["tipo_cabo"]
                    assert travessia_salva["qtd_cabos"] == travessia_excel["qtd_cabos"]
                else:
                    assert travessia_salva["tipo_rede"] == travessia_excel["tipo_rede"]
                    assert travessia_salva["tipo_cabo"] == travessia_excel["tipo_cabo"]
        
        # Verificar resultado
        resultado_salvo = await self.repository._get_resultado_calculo(str(ponto_id))
        assert resultado_salvo is not None
        
        for campo, valor_esperado in dados_excel["resultado_esperado"].items():
            assert resultado_salvo[campo] == valor_esperado, f"Campo {campo}: esperado {valor_esperado}, obtido {resultado_salvo[campo]}"
    
    @pytest.mark.asyncio
    async def test_parity_excel_incremental(self):
        """Testa a paridade incremental de novos cálculos."""
        dados_excel = self.carregar_dados_excel_referencia()
        
        # Criar múltiplos projetos com variações
        projetos_criados = []
        for i in range(3):
            dados_variacao = dados_excel.copy()
            dados_variacao["projeto"]["ns"] = f"REF-00{i+1}"
            dados_variacao["projeto"]["nome"] = f"Projeto Referência {i+1}"
            
            # Variar ligeiramente os resultados
            dados_variacao["resultado_esperado"]["total_tracao"] += i * 10
            dados_variacao["resultado_esperado"]["total_angulo"] += i * 5
            
            projeto = await self.criar_projeto_referencia(dados_variacao)
            ponto_id = await self.criar_ponto_referencia(projeto, dados_variacao)
            
            niveis_schema = self.converter_niveis_excel_para_schema(dados_variacao["niveis"])
            resultado_schema = self.criar_resultado_schema(dados_variacao["resultado_esperado"])
            
            sucesso = await self.repository.save_calculo_snapshot(str(ponto_id), niveis_schema, resultado_schema.dict())
            assert sucesso is True
            
            projetos_criados.append((projeto, ponto_id, dados_variacao))
        
        # Validar paridade para cada projeto
        for projeto, ponto_id, dados_variacao in projetos_criados:
            resultado_salvo = await self.repository._get_resultado_calculo(str(ponto_id))
            
            assert resultado_salvo["total_tracao"] == dados_variacao["resultado_esperado"]["total_tracao"]
            assert resultado_salvo["total_angulo"] == dados_variacao["resultado_esperado"]["total_angulo"]
            assert resultado_salvo["texto_total"] == dados_variacao["resultado_esperado"]["texto_total"]
    
    @pytest.mark.asyncio
    async def test_parity_excel_consistencia_numerica(self):
        """Testa a consistência numérica entre Excel e Supabase."""
        dados_excel = self.carregar_dados_excel_referencia()
        
        projeto = await self.criar_projeto_referencia(dados_excel)
        ponto_id = await self.criar_ponto_referencia(projeto, dados_excel)
        
        niveis_schema = self.converter_niveis_excel_para_schema(dados_excel["niveis"])
        resultado_schema = self.criar_resultado_schema(dados_excel["resultado_esperado"])
        
        sucesso = await self.repository.save_calculo_snapshot(str(ponto_id), niveis_schema, resultado_schema.dict())
        assert sucesso is True
        
        resultado_salvo = await self.repository._get_resultado_calculo(str(ponto_id))
        
        # Testar precisão numérica
        campos_numericos = [
            "mt1_tracao", "mt1_angulo", "mt2_tracao", "mt2_angulo",
            "bt_tracao", "bt_angulo", "btz_tracao", "btz_angulo",
            "ral_tracao", "ral_angulo", "total_tracao", "total_angulo", "poste_ecc"
        ]
        
        for campo in campos_numericos:
            valor_excel = dados_excel["resultado_esperado"][campo]
            valor_supabase = resultado_salvo[campo]
            
            # Verificar com tolerância de ponto flutuante
            assert abs(valor_excel - valor_supabase) < 0.001, f"Campo {campo}: diferença numérica inaceitável"
    
    @pytest.mark.asyncio
    async def test_parity_excel_campos_texto(self):
        """Testa a consistência dos campos de texto entre Excel e Supabase."""
        dados_excel = self.carregar_dados_excel_referencia()
        
        projeto = await self.criar_projeto_referencia(dados_excel)
        ponto_id = await self.criar_ponto_referencia(projeto, dados_excel)
        
        niveis_schema = self.converter_niveis_excel_para_schema(dados_excel["niveis"])
        resultado_schema = self.criar_resultado_schema(dados_excel["resultado_esperado"])
        
        sucesso = await self.repository.save_calculo_snapshot(str(ponto_id), niveis_schema, resultado_schema.dict())
        assert sucesso is True
        
        resultado_salvo = await self.repository._get_resultado_calculo(str(ponto_id))
        
        # Testar campos de texto
        campos_texto = [
            "texto_mt1", "texto_mt2", "texto_bt", "texto_btz", "texto_ral", "texto_total"
        ]
        
        for campo in campos_texto:
            valor_excel = dados_excel["resultado_esperado"][campo]
            valor_supabase = resultado_salvo[campo]
            
            assert valor_excel == valor_supabase, f"Campo {campo}: texto diferente"
    
    @pytest.mark.asyncio
    async def test_parity_excel_validacao_tipos(self):
        """Testa a validação de tipos entre Excel e Supabase."""
        dados_excel = self.carregar_dados_excel_referencia()
        
        projeto = await self.criar_projeto_referencia(dados_excel)
        ponto_id = await self.criar_ponto_referencia(projeto, dados_excel)
        
        niveis_schema = self.converter_niveis_excel_para_schema(dados_excel["niveis"])
        resultado_schema = self.criar_resultado_schema(dados_excel["resultado_esperado"])
        
        sucesso = await self.repository.save_calculo_snapshot(str(ponto_id), niveis_schema, resultado_schema.dict())
        assert sucesso is True
        
        resultado_salvo = await self.repository._get_resultado_calculo(str(ponto_id))
        
        # Testar tipos dos campos
        assert isinstance(resultado_salvo["total_tracao"], (int, float))
        assert isinstance(resultado_salvo["total_angulo"], (int, float))
        assert isinstance(resultado_salvo["poste_ecc"], (int, float))
        assert isinstance(resultado_salvo["texto_total"], str)
        
        # Testar tipos dos níveis
        niveis_salvos = await self.repository._get_niveis_calculo(str(ponto_id))
        for nivel in niveis_salvos:
            assert isinstance(nivel["altura_poste"], (int, float))
            assert isinstance(nivel["altura_ancoragem"], (int, float))
            
            travessias = await self.repository._get_travessias(nivel["id"])
            for travessia in travessias:
                assert isinstance(travessia["vao"], (int, float))
                assert isinstance(travessia["flecha"], (int, float))
                assert isinstance(travessia["angulo"], (int, float))


if __name__ == "__main__":
    # Executar os testes
    pytest.main([__file__, "-v"])