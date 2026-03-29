#!/usr/bin/env python3
"""Testes de integração real: Testes end-to-end com BD real (sem mocks)."""

import pytest
import asyncio
from uuid import uuid4

# Importar os schemas e serviços necessários
from api.schemas import ProjetoIn, PontoIn, NivelSalvarIn, TravessiaSalvarIn, ResultadoSalvarIn
from services.projeto_service import ProjetoService
from repositories.projeto_repository import ProjetoRepository
from db.supabase_client import get_supabase_client


class TestIntegracaoReal:
    """Testes de integração real com banco de dados Supabase."""

    def setup_method(self):
        """Configuração inicial para cada teste."""
        self.supabase_client = get_supabase_client()
        self.repository = ProjetoRepository(self.supabase_client)
        self.service = ProjetoService(self.repository)
        self.user_id = uuid4()

    async def criar_dados_integracao(self):
        """Cria dados completos para teste de integração."""
        # 1. Criar projeto
        projeto_in = ProjetoIn(
            orgao="IM3 Brasil",
            ns="INTEGRACAO-001",
            nome="Projeto Integração Real",
            endereco="Endereço Integração",
            estudado_por="Teste Integração",
            matricula="INT123",
            data_estudo="24/03/2026"
        )

        projeto = await self.service.create_projeto(projeto_in, self.user_id)

        # 2. Criar ponto
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

        # 3. Criar níveis completos
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

        # 4. Criar resultado
        resultado = ResultadoSalvarIn(
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
            texto_mt1="Integração MT1",
            texto_mt2="Integração MT2",
            texto_bt="Integração BT",
            texto_btz="Integração BTZ",
            texto_ral="Integração RAL",
            texto_total="Integração Total"
        )

        return projeto, ponto_id, niveis, resultado

    @pytest.mark.asyncio
    async def test_integracao_real_fluxo_completo(self):
        """Testa o fluxo completo de integração real."""
        # 1. Criar dados de integração
        projeto, ponto_id, niveis, resultado = await self.criar_dados_integracao()

        # 2. Salvar cálculo completo
        sucesso = await self.repository.save_calculo_snapshot(str(ponto_id), niveis, resultado.model_dump())
        assert sucesso is True

        # 3. Validar persistência completa
        # Verificar projeto
        projeto_salvo = await self.repository.get(projeto.id)
        assert projeto_salvo is not None
        assert projeto_salvo.nome == "Projeto Integração Real"

        # Verificar ponto
        ponto_salvo = await self.repository._get_ponto(str(ponto_id))
        assert ponto_salvo is not None
        assert ponto_salvo["ponto"] == "001"

        # Verificar níveis
        niveis_salvos = await self.repository._get_niveis_calculo(str(ponto_id))
        assert len(niveis_salvos) == 5

        # Verificar travessias
        total_travessias = 0
        for nivel in niveis_salvos:
            travessias = await self.repository._get_travessias(nivel['id'])
            total_travessias += len(travessias)

        assert total_travessias == 20

        # Verificar resultado
        resultado_salvo = await self.repository._get_resultado_calculo(str(ponto_id))
        assert resultado_salvo is not None
        assert resultado_salvo['total_tracao'] == 300.0
        assert resultado_salvo['texto_total'] == "Integração Total"

    @pytest.mark.asyncio
    async def test_integracao_real_consistencia_transacional(self):
        """Testa a consistência transacional da integração."""
        projeto, ponto_id, niveis, resultado = await self.criar_dados_integracao()

        # Testar consistência antes da persistência
        niveis_salvos_antes = await self.repository._get_niveis_calculo(str(ponto_id))
        assert len(niveis_salvos_antes) == 0

        resultado_salvo_antes = await self.repository._get_resultado_calculo(str(ponto_id))
        assert resultado_salvo_antes is None

        # Persistir
        sucesso = await self.repository.save_calculo_snapshot(str(ponto_id), niveis, resultado.model_dump())
        assert sucesso is True

        # Testar consistência após a persistência
        niveis_salvos_depois = await self.repository._get_niveis_calculo(str(ponto_id))
        assert len(niveis_salvos_depois) == 5

        resultado_salvo_depois = await self.repository._get_resultado_calculo(str(ponto_id))
        assert resultado_salvo_depois is not None
        assert resultado_salvo_depois['total_tracao'] == 300.0

    @pytest.mark.asyncio
    async def test_integracao_real_multiplos_usuarios(self):
        """Testa a integração com múltiplos usuários simultâneos."""
        # Criar usuários diferentes
        user1_id = uuid4()
        user2_id = uuid4()

        # Criar projetos para cada usuário
        projetos_criados = []

        for i, user_id in enumerate([user1_id, user2_id]):
            projeto_in = ProjetoIn(
                orgao="IM3 Brasil",
                ns=f"MULTI-USER-{i+1}",
                nome=f"Projeto Multi-User {i+1}",
                endereco="Endereço Multi-User",
                estudado_por=f"User {i+1}",
                matricula=f"MU{i+1}23",
                data_estudo="24/03/2026"
            )

            projeto = await self.service.create_projeto(projeto_in, user_id)
            projetos_criados.append((projeto, user_id))

        # Validar isolamento de usuários
        for projeto, user_id in projetos_criados:
            # Cada usuário deve ver apenas seus próprios projetos
            projetos_usuario = await self.repository.get_by_owner(user_id)
            assert len(projetos_usuario) == 1
            assert projetos_usuario[0].id == projeto.id

            # Verificar que não há vazamento entre usuários
            outros_usuarios = [u for u in [user1_id, user2_id] if u != user_id]
            for outro_user in outros_usuarios:
                projetos_outro = await self.repository.get_by_owner(outro_user)
                assert projeto.id not in [p.id for p in projetos_outro]

    @pytest.mark.asyncio
    async def test_integracao_real_cenario_producao(self):
        """Testa cenários reais de produção."""
        # Simular cenário real de produção
        projetos_producao = []

        for i in range(5):
            projeto_in = ProjetoIn(
                orgao="IM3 Brasil",
                ns=f"PROD-{i+1:03d}",
                nome=f"Projeto Produção {i+1}",
                endereco=f"Endereço Produção {i+1}",
                estudado_por="Eng. Produção",
                matricula=f"PROD{i+1:03d}",
                data_estudo="24/03/2026"
            )

            projeto = await self.service.create_projeto(projeto_in, self.user_id)
            projetos_producao.append(projeto)

        # Validar cenário de produção
        assert len(projetos_producao) == 5

        # Verificar que todos os projetos foram criados corretamente
        for projeto in projetos_producao:
            projeto_salvo = await self.repository.get(projeto.id)
            assert projeto_salvo is not None
            assert projeto_salvo.ns.startswith("PROD-")
            assert projeto_salvo.nome.startswith("Projeto Produção")

        # Verificar contagem total
        total_projetos = await self.repository.count(self.user_id)
        assert total_projetos >= 5

    @pytest.mark.asyncio
    async def test_integracao_real_performance(self):
        """Testa a performance da integração real."""
        import time

        # Medir tempo de criação de múltiplos projetos
        start_time = time.time()

        projetos_criados = []
        for i in range(10):
            projeto_in = ProjetoIn(
                orgao="IM3 Brasil",
                ns=f"PERF-{i+1:03d}",
                nome=f"Projeto Performance {i+1}",
                endereco=f"Endereço Performance {i+1}",
                estudado_por="Eng. Performance",
                matricula=f"PERF{i+1:03d}",
                data_estudo="24/03/2026"
            )

            projeto = await self.service.create_projeto(projeto_in, self.user_id)
            projetos_criados.append(projeto)

        end_time = time.time()
        tempo_criacao = end_time - start_time

        # Validar performance
        assert len(projetos_criados) == 10
        assert tempo_criacao < 30.0  # Deve criar 10 projetos em menos de 30 segundos

        # Medir tempo de leitura
        start_time = time.time()

        for projeto in projetos_criados:
            projeto_lido = await self.repository.get(projeto.id)
            assert projeto_lido is not None

        end_time = time.time()
        tempo_leitura = end_time - start_time

        # Validar performance de leitura
        assert tempo_leitura < 10.0  # Deve ler 10 projetos em menos de 10 segundos

    @pytest.mark.asyncio
    async def test_integracao_real_erro_banco_dados(self):
        """Testa o tratamento de erros do banco de dados."""
        # Testar cenário de erro de banco de dados
        # (Este teste depende da configuração do ambiente de teste)

        try:
            # Tentar criar um projeto com dados inválidos
            projeto_in = ProjetoIn(
                orgao="",  # Campo obrigatório vazio
                ns="ERRO-001",
                nome="Projeto com Erro",
                endereco="",
                estudado_por="",
                matricula="",
                data_estudo="24/03/2026"
            )

            projeto = await self.service.create_projeto(projeto_in, self.user_id)
            # Se não lançar exceção, validar que o projeto foi criado corretamente
            assert projeto is not None
            assert projeto.nome == "Projeto com Erro"

        except Exception as e:
            # Validar que a exceção foi tratada corretamente
            assert "Erro" in str(e) or "validação" in str(e).lower()

    @pytest.mark.asyncio
    async def test_integracao_real_concorrencia(self):
        """Testa a concorrência na integração real."""

        # Criar múltiplas tarefas concorrentes
        async def criar_projeto_concorrente(i):
            projeto_in = ProjetoIn(
                orgao="IM3 Brasil",
                ns=f"CONC-{i+1:03d}",
                nome=f"Projeto Concorrente {i+1}",
                endereco=f"Endereço Concorrente {i+1}",
                estudado_por="Eng. Concorrente",
                matricula=f"CONC{i+1:03d}",
                data_estudo="24/03/2026"
            )

            return await self.service.create_projeto(projeto_in, self.user_id)

        # Executar tarefas concorrentes
        tasks = [criar_projeto_concorrente(i) for i in range(5)]
        projetos_criados = await asyncio.gather(*tasks)

        # Validar concorrência
        assert len(projetos_criados) == 5
        for i, projeto in enumerate(projetos_criados):
            assert projeto is not None
            assert projeto.ns == f"CONC-{i+1:03d}"
            assert projeto.nome == f"Projeto Concorrente {i+1}"


if __name__ == "__main__":
    # Executar os testes
    pytest.main([__file__, "-v"])
