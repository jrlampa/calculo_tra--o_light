#!/usr/bin/env python3
"""Testes de persistência de cálculos: POST /calcular → resultados_calculo."""

import pytest
from uuid import uuid4

# Importar os schemas e serviços necessários
from api.schemas import CalculoInput, ProjetoIn, PontoIn, ResultadoSalvarIn
from services.projeto_service import ProjetoService
from repositories.projeto_repository import ProjetoRepository
from db.supabase_client import get_supabase_client


class TestPersistenciaCalculo:
    """Testes para validar a persistência de cálculos."""

    def setup_method(self):
        """Configuração inicial para cada teste."""
        self.supabase_client = get_supabase_client()
        self.repository = ProjetoRepository(self.supabase_client)
        self.service = ProjetoService(self.repository)
        self.user_id = uuid4()

    async def criar_projeto_e_ponto_teste(self):
        """Cria um projeto e ponto de teste."""
        # Criar projeto
        projeto_in = ProjetoIn(
            orgao="IM3 Brasil",
            ns="TESTE-CALC",
            nome="Projeto Teste Cálculo",
            endereco="Endereço Teste",
            estudado_por="Teste User",
            matricula="12345",
            data_estudo="24/03/2026"
        )

        projeto = await self.service.create_projeto(projeto_in, self.user_id)

        # Criar ponto
        ponto_in = PontoIn(
            ponto="001",
            tipo_poste="DT",
            modelo_poste="11/600"
        )

        ponto_id = await self.repository.save_ponto(
            str(projeto.id),
            ponto_in.ponto,
            ponto_in.tipo_poste,
            ponto_in.modelo_poste
        )

        return projeto, ponto_id

    def criar_calculo_input_teste(self):
        """Cria um input de cálculo de teste."""
        return CalculoInput(
            cabecalho={
                "orgao": "IM3 Brasil",
                "ns": "TESTE-CALC",
                "projeto": "Projeto Teste Cálculo",
                "ponto": "001",
                "endereco": "Endereço Teste",
                "estudado_por": "Teste User",
                "matricula": "12345",
                "data": "24/03/2026"
            },
            poste={
                "tipo_poste": "DT",
                "modelo_poste": "11/600"
            },
            mt1=[
                {"tipo_rede": "Convencional", "tipo_cabo": "397MCM-CA, Nu", "vao": 33.0, "flecha": 0.5, "angulo": 0.0, "altura_poste": 11.0, "altura_ancoragem": 9.2},
                {"tipo_rede": "Convencional", "tipo_cabo": "397MCM-CA, Nu", "vao": 33.0, "flecha": 0.5, "angulo": 0.0, "altura_poste": 11.0, "altura_ancoragem": 9.2},
                {"tipo_rede": "Convencional", "tipo_cabo": "397MCM-CA, Nu", "vao": 33.0, "flecha": 0.5, "angulo": 0.0, "altura_poste": 11.0, "altura_ancoragem": 9.2},
                {"tipo_rede": "Convencional", "tipo_cabo": "397MCM-CA, Nu", "vao": 33.0, "flecha": 0.5, "angulo": 0.0, "altura_poste": 11.0, "altura_ancoragem": 9.2}
            ],
            mt2=[
                {"tipo_rede": "Convencional", "tipo_cabo": "397MCM-CA, Nu", "vao": 33.0, "flecha": 0.5, "angulo": 0.0, "altura_poste": 11.0, "altura_ancoragem": 9.2},
                {"tipo_rede": "Convencional", "tipo_cabo": "397MCM-CA, Nu", "vao": 33.0, "flecha": 0.5, "angulo": 0.0, "altura_poste": 11.0, "altura_ancoragem": 9.2},
                {"tipo_rede": "Convencional", "tipo_cabo": "397MCM-CA, Nu", "vao": 33.0, "flecha": 0.5, "angulo": 0.0, "altura_poste": 11.0, "altura_ancoragem": 9.2},
                {"tipo_rede": "Convencional", "tipo_cabo": "397MCM-CA, Nu", "vao": 33.0, "flecha": 0.5, "angulo": 0.0, "altura_poste": 11.0, "altura_ancoragem": 9.2}
            ],
            bt=[
                {"tipo_rede": "Convencional", "tipo_cabo": "397MCM-CA, Nu", "vao": 33.0, "flecha": 0.5, "angulo": 0.0, "altura_poste": 11.0, "altura_ancoragem": 9.2},
                {"tipo_rede": "Convencional", "tipo_cabo": "397MCM-CA, Nu", "vao": 33.0, "flecha": 0.5, "angulo": 0.0, "altura_poste": 11.0, "altura_ancoragem": 9.2},
                {"tipo_rede": "Convencional", "tipo_cabo": "397MCM-CA, Nu", "vao": 33.0, "flecha": 0.5, "angulo": 0.0, "altura_poste": 11.0, "altura_ancoragem": 9.2},
                {"tipo_rede": "Convencional", "tipo_cabo": "397MCM-CA, Nu", "vao": 33.0, "flecha": 0.5, "angulo": 0.0, "altura_poste": 11.0, "altura_ancoragem": 9.2}
            ],
            btz=[
                {"qtd_ligacoes": 2, "vao": 33.0, "flecha": 0.5, "angulo": 0.0, "altura_poste": 11.0, "altura_ancoragem": 9.2},
                {"qtd_ligacoes": 2, "vao": 33.0, "flecha": 0.5, "angulo": 0.0, "altura_poste": 11.0, "altura_ancoragem": 9.2},
                {"qtd_ligacoes": 2, "vao": 33.0, "flecha": 0.5, "angulo": 0.0, "altura_poste": 11.0, "altura_ancoragem": 9.2},
                {"qtd_ligacoes": 2, "vao": 33.0, "flecha": 0.5, "angulo": 0.0, "altura_poste": 11.0, "altura_ancoragem": 9.2}
            ],
            ral=[
                {"tipo_cabo": "397MCM-CA, Nu", "qtd_cabos": 3, "vao": 33.0, "flecha": 0.5, "angulo": 0.0, "altura_poste": 11.0, "altura_ancoragem": 9.2},
                {"tipo_cabo": "397MCM-CA, Nu", "qtd_cabos": 3, "vao": 33.0, "flecha": 0.5, "angulo": 0.0, "altura_poste": 11.0, "altura_ancoragem": 9.2},
                {"tipo_cabo": "397MCM-CA, Nu", "qtd_cabos": 3, "vao": 33.0, "flecha": 0.5, "angulo": 0.0, "altura_poste": 11.0, "altura_ancoragem": 9.2},
                {"tipo_cabo": "397MCM-CA, Nu", "qtd_cabos": 3, "vao": 33.0, "flecha": 0.5, "angulo": 0.0, "altura_poste": 11.0, "altura_ancoragem": 9.2}
            ]
        )

    def criar_resultado_teste(self):
        """Cria um resultado de teste."""
        return ResultadoSalvarIn(
            mt1_tracao=100.0,
            mt1_angulo=0.0,
            mt2_tracao=100.0,
            mt2_angulo=0.0,
            bt_tracao=50.0,
            bt_angulo=0.0,
            btz_tracao=30.0,
            btz_angulo=0.0,
            ral_tracao=20.0,
            ral_angulo=0.0,
            total_tracao=300.0,
            total_angulo=0.0,
            poste_ecc=150.0,
            texto_mt1="Teste MT1",
            texto_mt2="Teste MT2",
            texto_bt="Teste BT",
            texto_btz="Teste BTZ",
            texto_ral="Teste RAL",
            texto_total="Teste Total"
        )

    @pytest.mark.asyncio
    async def test_persistencia_calculo_fluxo_completo(self):
        """Testa o fluxo completo de persistência de cálculo."""
        # 1. Criar projeto e ponto
        projeto, ponto_id = await self.criar_projeto_e_ponto_teste()

        # 2. Criar input de cálculo
        calculo_input = self.criar_calculo_input_teste()

        # 3. Simular cálculo (aqui usamos valores fixos para teste)
        resultado = self.criar_resultado_teste()

        # 4. Salvar cálculo
        sucesso = await self.repository.save_calculo_snapshot(str(ponto_id), calculo_input, resultado.model_dump())
        assert sucesso is True

        # 5. Validar persistência
        # Verificar se o resultado foi salvo
        resultado_salvo = await self.repository._get_resultado_calculo(str(ponto_id))
        assert resultado_salvo is not None
        assert resultado_salvo['total_tracao'] == 300.0
        assert resultado_salvo['total_angulo'] == 0.0
        assert resultado_salvo['poste_ecc'] == 150.0
        assert resultado_salvo['texto_total'] == "Teste Total"

        # Verificar se os níveis foram salvos
        niveis_salvos = await self.repository._get_niveis_calculo(str(ponto_id))
        assert len(niveis_salvos) == 5  # MT1, MT2, BT, BTZ, RAL

        # Verificar se as travessias foram salvas
        total_travessias = 0
        for nivel in niveis_salvos:
            travessias = await self.repository._get_travessias(nivel['id'])
            total_travessias += len(travessias)

        assert total_travessias == 20  # 5 níveis × 4 travessias cada

    @pytest.mark.asyncio
    async def test_persistencia_calculo_atualizacao(self):
        """Testa a atualização de resultados de cálculo existentes."""
        # Criar projeto e ponto
        projeto, ponto_id = await self.criar_projeto_e_ponto_teste()

        # Primeiro cálculo
        resultado1 = ResultadoSalvarIn(
            mt1_tracao=100.0,
            mt1_angulo=0.0,
            mt2_tracao=100.0,
            mt2_angulo=0.0,
            bt_tracao=50.0,
            bt_angulo=0.0,
            btz_tracao=30.0,
            btz_angulo=0.0,
            ral_tracao=20.0,
            ral_angulo=0.0,
            total_tracao=300.0,
            total_angulo=0.0,
            poste_ecc=150.0,
            texto_mt1="Primeiro cálculo",
            texto_mt2="Primeiro cálculo",
            texto_bt="Primeiro cálculo",
            texto_btz="Primeiro cálculo",
            texto_ral="Primeiro cálculo",
            texto_total="Primeiro cálculo"
        )

        sucesso1 = await self.repository.save_calculo_snapshot(str(ponto_id), [], resultado1.model_dump())
        assert sucesso1 is True

        # Validar primeiro cálculo
        resultado_salvo1 = await self.repository._get_resultado_calculo(str(ponto_id))
        assert resultado_salvo1['texto_total'] == "Primeiro cálculo"
        assert resultado_salvo1['total_tracao'] == 300.0

        # Segundo cálculo (atualização)
        resultado2 = ResultadoSalvarIn(
            mt1_tracao=120.0,
            mt1_angulo=5.0,
            mt2_tracao=120.0,
            mt2_angulo=5.0,
            bt_tracao=60.0,
            bt_angulo=5.0,
            btz_tracao=35.0,
            btz_angulo=5.0,
            ral_tracao=25.0,
            ral_angulo=5.0,
            total_tracao=360.0,
            total_angulo=5.0,
            poste_ecc=180.0,
            texto_mt1="Segundo cálculo",
            texto_mt2="Segundo cálculo",
            texto_bt="Segundo cálculo",
            texto_btz="Segundo cálculo",
            texto_ral="Segundo cálculo",
            texto_total="Segundo cálculo"
        )

        sucesso2 = await self.repository.save_calculo_snapshot(str(ponto_id), [], resultado2.model_dump())
        assert sucesso2 is True

        # Validar atualização
        resultado_salvo2 = await self.repository._get_resultado_calculo(str(ponto_id))
        assert resultado_salvo2['texto_total'] == "Segundo cálculo"
        assert resultado_salvo2['total_tracao'] == 360.0
        assert resultado_salvo2['total_angulo'] == 5.0
        assert resultado_salvo2['poste_ecc'] == 180.0

    @pytest.mark.asyncio
    async def test_persistencia_calculo_consistencia_dados(self):
        """Testa a consistência dos dados persistidos."""
        projeto, ponto_id = await self.criar_projeto_e_ponto_teste()

        # Criar cálculo com dados específicos
        resultado = ResultadoSalvarIn(
            mt1_tracao=150.5,
            mt1_angulo=12.3,
            mt2_tracao=140.2,
            mt2_angulo=15.7,
            bt_tracao=80.8,
            bt_angulo=8.9,
            btz_tracao=45.3,
            btz_angulo=25.4,
            ral_tracao=35.1,
            ral_angulo=45.2,
            total_tracao=451.9,
            total_angulo=107.5,
            poste_ecc=225.95,
            texto_mt1="MT1 detalhado",
            texto_mt2="MT2 detalhado",
            texto_bt="BT detalhado",
            texto_btz="BTZ detalhado",
            texto_ral="RAL detalhado",
            texto_total="Resultado detalhado"
        )

        sucesso = await self.repository.save_calculo_snapshot(str(ponto_id), [], resultado.model_dump())
        assert sucesso is True

        # Validar consistência dos dados
        resultado_salvo = await self.repository._get_resultado_calculo(str(ponto_id))

        # Verificar tipos e valores
        assert isinstance(resultado_salvo['total_tracao'], (int, float))
        assert isinstance(resultado_salvo['total_angulo'], (int, float))
        assert isinstance(resultado_salvo['poste_ecc'], (int, float))
        assert isinstance(resultado_salvo['texto_total'], str)

        # Verificar valores específicos
        assert abs(resultado_salvo['total_tracao'] - 451.9) < 0.01
        assert abs(resultado_salvo['total_angulo'] - 107.5) < 0.01
        assert abs(resultado_salvo['poste_ecc'] - 225.95) < 0.01
        assert resultado_salvo['texto_total'] == "Resultado detalhado"

    @pytest.mark.asyncio
    async def test_persistencia_calculo_multiplos_pontos(self):
        """Testa a persistência de cálculos em múltiplos pontos."""
        projeto, ponto_id1 = await self.criar_projeto_e_ponto_teste()

        # Criar segundo ponto
        ponto_in2 = PontoIn(
            ponto="002",
            tipo_poste="DT",
            modelo_poste="11/600"
        )

        ponto_id2 = await self.repository.save_ponto(
            str(projeto.id),
            ponto_in2.ponto,
            ponto_in2.tipo_poste,
            ponto_in2.modelo_poste
        )

        # Calcular resultados diferentes para cada ponto
        resultado1 = ResultadoSalvarIn(
            mt1_tracao=100.0, mt1_angulo=0.0, mt2_tracao=100.0, mt2_angulo=0.0,
            bt_tracao=50.0, bt_angulo=0.0, btz_tracao=30.0, btz_angulo=0.0,
            ral_tracao=20.0, ral_angulo=0.0, total_tracao=300.0, total_angulo=0.0,
            poste_ecc=150.0, texto_mt1="Ponto 1", texto_mt2="Ponto 1",
            texto_bt="Ponto 1", texto_btz="Ponto 1", texto_ral="Ponto 1",
            texto_total="Ponto 1"
        )

        resultado2 = ResultadoSalvarIn(
            mt1_tracao=120.0, mt1_angulo=5.0, mt2_tracao=120.0, mt2_angulo=5.0,
            bt_tracao=60.0, bt_angulo=5.0, btz_tracao=35.0, btz_angulo=5.0,
            ral_tracao=25.0, ral_angulo=5.0, total_tracao=360.0, total_angulo=5.0,
            poste_ecc=180.0, texto_mt1="Ponto 2", texto_mt2="Ponto 2",
            texto_bt="Ponto 2", texto_btz="Ponto 2", texto_ral="Ponto 2",
            texto_total="Ponto 2"
        )

        # Salvar cálculos em ambos os pontos
        sucesso1 = await self.repository.save_calculo_snapshot(str(ponto_id1), [], resultado1.model_dump())
        sucesso2 = await self.repository.save_calculo_snapshot(str(ponto_id2), [], resultado2.model_dump())

        assert sucesso1 is True
        assert sucesso2 is True

        # Validar resultados independentes
        resultado1_salvo = await self.repository._get_resultado_calculo(str(ponto_id1))
        resultado2_salvo = await self.repository._get_resultado_calculo(str(ponto_id2))

        assert resultado1_salvo['texto_total'] == "Ponto 1"
        assert resultado1_salvo['total_tracao'] == 300.0
        assert resultado2_salvo['texto_total'] == "Ponto 2"
        assert resultado2_salvo['total_tracao'] == 360.0

        # Verificar que os resultados são independentes
        assert resultado1_salvo['total_tracao'] != resultado2_salvo['total_tracao']
        assert resultado1_salvo['texto_total'] != resultado2_salvo['texto_total']

    @pytest.mark.asyncio
    async def test_persistencia_calculo_validacao_campos(self):
        """Testa a validação dos campos na persistência de cálculo."""
        projeto, ponto_id = await self.criar_projeto_e_ponto_teste()

        # Testar validação de campos numéricos
        testes_validacao = [
            # Valores negativos (devem ser rejeitados)
            {'total_tracao': -100.0, 'expected_error': True},
            {'total_angulo': -5.0, 'expected_error': True},
            {'poste_ecc': -50.0, 'expected_error': True},

            # Valores normais (devem ser aceitos)
            {'total_tracao': 100.0, 'total_angulo': 0.0, 'poste_ecc': 50.0, 'expected_error': False},
            {'total_tracao': 0.0, 'total_angulo': 0.0, 'poste_ecc': 0.0, 'expected_error': False},
        ]

        for teste in testes_validacao:
            try:
                resultado = ResultadoSalvarIn(
                    mt1_tracao=100.0, mt1_angulo=0.0, mt2_tracao=100.0, mt2_angulo=0.0,
                    bt_tracao=50.0, bt_angulo=0.0, btz_tracao=30.0, btz_angulo=0.0,
                    ral_tracao=20.0, ral_angulo=0.0,
                    total_tracao=teste.get('total_tracao', 300.0),
                    total_angulo=teste.get('total_angulo', 0.0),
                    poste_ecc=teste.get('poste_ecc', 150.0),
                    texto_mt1="Teste", texto_mt2="Teste", texto_bt="Teste",
                    texto_btz="Teste", texto_ral="Teste", texto_total="Teste"
                )
                sucesso = await self.repository.save_calculo_snapshot(str(ponto_id), [], resultado.model_dump())
                if teste['expected_error']:
                    assert sucesso is False, f"Deveria ter falhado para valores: {teste}"
                else:
                    assert sucesso is True, f"Deveria ter sucesso para valores: {teste}"
            except Exception as e:
                if teste['expected_error']:
                    # Erro esperado
                    pass
                else:
                    # Erro inesperado
                    raise e


if __name__ == "__main__":
    # Executar os testes
    pytest.main([__file__, "-v"])
