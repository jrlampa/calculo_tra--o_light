#!/usr/bin/env python3
"""Testes de hierarquia completa: Projeto → Ponto → Nível → Travessia."""

import pytest
from uuid import uuid4

# Importar os schemas e serviços necessários
from api.schemas import ProjetoIn, PontoIn, NivelSalvarIn, TravessiaSalvarIn, ResultadoSalvarIn, SalvarCalculoIn
from services.projeto_service import ProjetoService
from repositories.projeto_repository import ProjetoRepository
from db.supabase_client import get_supabase_client


class TestHierarquiaCompleta:
    """Testes para validar a hierarquia completa de persistência."""

    def setup_method(self):
        """Configuração inicial para cada teste."""
        self.supabase_client = get_supabase_client()
        self.repository = ProjetoRepository(self.supabase_client)
        self.service = ProjetoService(self.repository)
        self.user_id = uuid4()

    async def criar_projeto_teste(self):
        """Cria um projeto de teste."""
        projeto_in = ProjetoIn(
            orgao="IM3 Brasil",
            ns="TESTE-123",
            nome="Projeto de Teste Hierarquia",
            endereco="Endereço Teste",
            estudado_por="Teste User",
            matricula="12345",
            data_estudo="24/03/2026"
        )

        projeto = await self.service.create_projeto(projeto_in, self.user_id)
        return projeto

    async def criar_ponto_teste(self, projeto_id):
        """Cria um ponto de teste."""
        ponto_in = PontoIn(
            ponto="001",
            tipo_poste="DT",
            modelo_poste="11/600"
        )

        # Simular a criação do ponto (precisamos do método no serviço)
        ponto_id = await self.repository.save_ponto(
            str(projeto_id),
            ponto_in.ponto,
            ponto_in.tipo_poste,
            ponto_in.modelo_poste
        )
        return ponto_id

    def criar_niveis_teste(self):
        """Cria níveis de teste para todos os tipos."""
        niveis = []

        # MT1
        mt1_travessias = [
            TravessiaSalvarIn(posicao=1, tipo_rede="Convencional", tipo_cabo="397MCM-CA, Nu", vao=33.0, flecha=0.5, angulo=0.0),
            TravessiaSalvarIn(posicao=2, tipo_rede="Convencional", tipo_cabo="397MCM-CA, Nu", vao=33.0, flecha=0.5, angulo=0.0),
            TravessiaSalvarIn(posicao=3, tipo_rede="Convencional", tipo_cabo="397MCM-CA, Nu", vao=33.0, flecha=0.5, angulo=0.0),
            TravessiaSalvarIn(posicao=4, tipo_rede="Convencional", tipo_cabo="397MCM-CA, Nu", vao=33.0, flecha=0.5, angulo=0.0),
        ]
        niveis.append(NivelSalvarIn(nivel="MT1", altura_poste=11.0, altura_ancoragem=9.2, travessias=mt1_travessias))

        # MT2
        mt2_travessias = [
            TravessiaSalvarIn(posicao=1, tipo_rede="Convencional", tipo_cabo="397MCM-CA, Nu", vao=33.0, flecha=0.5, angulo=0.0),
            TravessiaSalvarIn(posicao=2, tipo_rede="Convencional", tipo_cabo="397MCM-CA, Nu", vao=33.0, flecha=0.5, angulo=0.0),
            TravessiaSalvarIn(posicao=3, tipo_rede="Convencional", tipo_cabo="397MCM-CA, Nu", vao=33.0, flecha=0.5, angulo=0.0),
            TravessiaSalvarIn(posicao=4, tipo_rede="Convencional", tipo_cabo="397MCM-CA, Nu", vao=33.0, flecha=0.5, angulo=0.0),
        ]
        niveis.append(NivelSalvarIn(nivel="MT2", altura_poste=11.0, altura_ancoragem=9.2, travessias=mt2_travessias))

        # BT
        bt_travessias = [
            TravessiaSalvarIn(posicao=1, tipo_rede="Convencional", tipo_cabo="397MCM-CA, Nu", vao=33.0, flecha=0.5, angulo=0.0),
            TravessiaSalvarIn(posicao=2, tipo_rede="Convencional", tipo_cabo="397MCM-CA, Nu", vao=33.0, flecha=0.5, angulo=0.0),
            TravessiaSalvarIn(posicao=3, tipo_rede="Convencional", tipo_cabo="397MCM-CA, Nu", vao=33.0, flecha=0.5, angulo=0.0),
            TravessiaSalvarIn(posicao=4, tipo_rede="Convencional", tipo_cabo="397MCM-CA, Nu", vao=33.0, flecha=0.5, angulo=0.0),
        ]
        niveis.append(NivelSalvarIn(nivel="BT", altura_poste=11.0, altura_ancoragem=9.2, travessias=bt_travessias))

        # BTZ
        btz_travessias = [
            TravessiaSalvarIn(posicao=1, qtd_ligacoes=2, vao=33.0, flecha=0.5, angulo=0.0),
            TravessiaSalvarIn(posicao=2, qtd_ligacoes=2, vao=33.0, flecha=0.5, angulo=0.0),
            TravessiaSalvarIn(posicao=3, qtd_ligacoes=2, vao=33.0, flecha=0.5, angulo=0.0),
            TravessiaSalvarIn(posicao=4, qtd_ligacoes=2, vao=33.0, flecha=0.5, angulo=0.0),
        ]
        niveis.append(NivelSalvarIn(nivel="BTZ", altura_poste=11.0, altura_ancoragem=9.2, travessias=btz_travessias))

        # RAL
        ral_travessias = [
            TravessiaSalvarIn(posicao=1, tipo_cabo="397MCM-CA, Nu", qtd_cabos=3, vao=33.0, flecha=0.5, angulo=0.0),
            TravessiaSalvarIn(posicao=2, tipo_cabo="397MCM-CA, Nu", qtd_cabos=3, vao=33.0, flecha=0.5, angulo=0.0),
            TravessiaSalvarIn(posicao=3, tipo_cabo="397MCM-CA, Nu", qtd_cabos=3, vao=33.0, flecha=0.5, angulo=0.0),
            TravessiaSalvarIn(posicao=4, tipo_cabo="397MCM-CA, Nu", qtd_cabos=3, vao=33.0, flecha=0.5, angulo=0.0),
        ]
        niveis.append(NivelSalvarIn(nivel="RAL", altura_poste=11.0, altura_ancoragem=9.2, travessias=ral_travessias))

        return niveis

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
    async def test_hierarquia_completa_fluxo(self):
        """Testa o fluxo completo: Projeto → Ponto → Níveis → Travessias → Resultado."""
        # 1. Criar projeto
        projeto = await self.criar_projeto_teste()
        assert projeto is not None
        assert projeto.nome == "Projeto de Teste Hierarquia"

        # 2. Criar ponto
        ponto_id = await self.criar_ponto_teste(projeto.id)
        assert ponto_id is not None

        # 3. Criar níveis e travessias
        niveis = self.criar_niveis_teste()
        assert len(niveis) == 5  # MT1, MT2, BT, BTZ, RAL

        # 4. Salvar cálculo completo
        resultado = self.criar_resultado_teste()

        SalvarCalculoIn(
            ponto_id=ponto_id,
            niveis=niveis,
            resultado=resultado
        )

        # Testar a persistência do cálculo
        sucesso = await self.repository.save_calculo_snapshot(str(ponto_id), niveis, resultado.model_dump())
        assert sucesso is True

        # 5. Validar persistência
        # Verificar se os níveis foram salvos
        niveis_salvos = await self.repository._get_niveis_calculo(str(ponto_id))
        assert len(niveis_salvos) == 5

        # Verificar se as travessias foram salvas
        total_travessias = 0
        for nivel in niveis_salvos:
            travessias = await self.repository._get_travessias(nivel['id'])
            total_travessias += len(travessias)

        assert total_travessias == 20  # 5 níveis × 4 travessias cada

        # Verificar se o resultado foi salvo
        resultado_salvo = await self.repository._get_resultado_calculo(str(ponto_id))
        assert resultado_salvo is not None
        assert resultado_salvo['total_tracao'] == 300.0

    @pytest.mark.asyncio
    async def test_hierarquia_completa_multiplos_pontos(self):
        """Testa a hierarquia completa com múltiplos pontos no mesmo projeto."""
        # Criar projeto
        projeto = await self.criar_projeto_teste()

        # Criar múltiplos pontos
        pontos_ids = []
        for i in range(3):
            ponto_id = await self.criar_ponto_teste(projeto.id)
            pontos_ids.append(ponto_id)

        assert len(pontos_ids) == 3

        # Criar hierarquia para cada ponto
        for ponto_id in pontos_ids:
            niveis = self.criar_niveis_teste()
            resultado = self.criar_resultado_teste()

            sucesso = await self.repository.save_calculo_snapshot(str(ponto_id), niveis, resultado.model_dump())
            assert sucesso is True

        # Validar que todos os pontos têm hierarquia completa
        for ponto_id in pontos_ids:
            niveis_salvos = await self.repository._get_niveis_calculo(str(ponto_id))
            assert len(niveis_salvos) == 5

            total_travessias = 0
            for nivel in niveis_salvos:
                travessias = await self.repository._get_travessias(nivel['id'])
                total_travessias += len(travessias)

            assert total_travessias == 20

    @pytest.mark.asyncio
    async def test_hierarquia_completa_validacao_campos(self):
        """Testa a validação dos campos na hierarquia completa."""
        projeto = await self.criar_projeto_teste()
        await self.criar_ponto_teste(projeto.id)

        # Testar validação de níveis
        niveis = self.criar_niveis_teste()

        # Validar que todos os níveis têm os campos corretos
        for nivel in niveis:
            assert nivel.nivel in ["MT1", "MT2", "BT", "BTZ", "RAL"]
            assert nivel.altura_poste > 0
            assert nivel.altura_ancoragem > 0
            assert len(nivel.travessias) == 4

            # Validar travessias
            for travessia in nivel.travessias:
                assert travessia.posicao in [1, 2, 3, 4]
                assert travessia.vao >= 0
                assert travessia.flecha >= 0
                assert travessia.angulo >= 0

    @pytest.mark.asyncio
    async def test_hierarquia_completa_consistencia_referencial(self):
        """Testa a consistência referencial entre as tabelas."""
        projeto = await self.criar_projeto_teste()
        ponto_id = await self.criar_ponto_teste(projeto.id)

        niveis = self.criar_niveis_teste()
        resultado = self.criar_resultado_teste()

        # Salvar hierarquia
        sucesso = await self.repository.save_calculo_snapshot(str(ponto_id), niveis, resultado.model_dump())
        assert sucesso is True

        # Validar consistência referencial
        # 1. Verificar que o ponto pertence ao projeto
        ponto = await self.repository._get_ponto(str(ponto_id))
        assert ponto['projeto_id'] == str(projeto.id)

        # 2. Verificar que os níveis pertencem ao ponto
        niveis_salvos = await self.repository._get_niveis_calculo(str(ponto_id))
        for nivel in niveis_salvos:
            assert nivel['ponto_id'] == str(ponto_id)

        # 3. Verificar que as travessias pertencem aos níveis
        for nivel in niveis_salvos:
            travessias = await self.repository._get_travessias(nivel['id'])
            for travessia in travessias:
                assert travessia['nivel_id'] == str(nivel['id'])

        # 4. Verificar que o resultado pertence ao ponto
        resultado_salvo = await self.repository._get_resultado_calculo(str(ponto_id))
        assert resultado_salvo['ponto_id'] == str(ponto_id)


if __name__ == "__main__":
    # Executar os testes
    pytest.main([__file__, "-v"])
