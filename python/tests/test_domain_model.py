"""Tests for domain model — ensure aggregates and invariants work correctly.

No database, no HTTP — pure domain logic validation.
"""
import pytest
from datetime import datetime
from uuid import uuid4

from domain import (
    Projeto,
    Poste,
    Nivel,
    Travessia,
    Condutor,
    Geometria,
    CalculoResultado,
    NivelEnum,
    TipoPoste,
    TipoRede,
    CaboConductor,
    PosteId,
    ProjetoId,
    DuplicatePosteNumero,
    InvalidNivelStructure,
    NoCálculoDraft,
    PosteNotFound,
)


class TestProjetoAggregate:
    """Tests for Projeto aggregate root."""

    def test_criar_projeto_valido(self):
        """A Projeto can be created with required fields."""
        proj = Projeto(
            owner_id="user123",
            nome="Projeto Light RJ",
            endereco="Rua X nº 100",
            orgao="LIGHT S.A.",
            ns="LT-RJ-001",
        )
        assert proj.owner_id == "user123"
        assert proj.nome == "Projeto Light RJ"
        assert not proj.esta_deletado()

    def test_projeto_rejeita_owner_vazio(self):
        """Projeto requires owner_id."""
        with pytest.raises(ValueError, match="owner_id"):
            Projeto(owner_id="", nome="Test")

    def test_projeto_rejeita_nome_vazio(self):
        """Projeto requires nome."""
        with pytest.raises(ValueError, match="nome"):
            Projeto(owner_id="user1", nome="")

    def test_projeto_adiciona_poste_id(self):
        """Projeto can add a Poste ID."""
        proj = Projeto(owner_id="user1", nome="Test")
        poste_id = PosteId()
        proj.adicionar_poste_id(poste_id)
        assert poste_id in proj.poste_ids

    def test_projeto_rejeita_duplicado_poste_id(self):
        """Projeto rejects duplicate Poste IDs."""
        proj = Projeto(owner_id="user1", nome="Test")
        poste_id = PosteId()
        proj.adicionar_poste_id(poste_id)
        with pytest.raises(ValueError, match="já foi adicionado"):
            proj.adicionar_poste_id(poste_id)

    def test_projeto_remove_poste_id(self):
        """Projeto can remove a Poste ID."""
        proj = Projeto(owner_id="user1", nome="Test")
        poste_id = PosteId()
        proj.adicionar_poste_id(poste_id)
        proj.remover_poste_id(poste_id)
        assert poste_id not in proj.poste_ids

    def test_projeto_delete_soft(self):
        """Projeto can be soft-deleted."""
        proj = Projeto(owner_id="user1", nome="Test")
        assert not proj.esta_deletado()
        proj.deletar()
        assert proj.esta_deletado()
        assert proj.deletado_em is not None


class TestPosteAggregate:
    """Tests for Poste aggregate root."""

    def _criar_travessia_default(self, posicao: int) -> Travessia:
        """Create a default Travessia for testing."""
        return Travessia(
            posicao=posicao,
            condutor=Condutor(
                tipo_rede=TipoRede.CIRCUITO,
                tipo_cabo=CaboConductor.CAA,
                qtd_ligacoes=2,
                qtd_cabos=3,
            ),
            geometria=Geometria(vao=15.0, flecha=0.5, angulo=10.0),
        )

    def _criar_nivel_default(self, nivel_enum: NivelEnum) -> Nivel:
        """Create a default Nivel for testing."""
        return Nivel(
            nivel_enum=nivel_enum,
            altura_poste=11.0 - nivel_enum.ordem() * 0.5,  # decreasing
            altura_ancoragem=9.0 - nivel_enum.ordem() * 0.5,
            travessias=[
                self._criar_travessia_default(posicao)
                for posicao in range(1, 5)
            ],
        )

    def test_criar_poste_valido(self):
        """A Poste can be created with all required structure."""
        niveis = [self._criar_nivel_default(ne) for ne in NivelEnum]
        poste = Poste(
            projeto_id=ProjetoId(),
            numero="P001",
            tipo_poste=TipoPoste.CONCRETO,
            modelo_poste="11/600",
            niveis=niveis,
        )
        assert poste.numero == "P001"
        assert len(poste.niveis) == 5
        assert not poste.esta_deletado()

    def test_poste_rejeita_numero_vazio(self):
        """Poste requires numero."""
        niveis = [self._criar_nivel_default(ne) for ne in NivelEnum]
        with pytest.raises(ValueError, match="numero"):
            Poste(
                projeto_id=ProjetoId(),
                numero="",
                tipo_poste=TipoPoste.CONCRETO,
                niveis=niveis,
            )

    def test_poste_rejeita_menos_de_5_niveis(self):
        """Poste must have exactly 5 Niveis."""
        niveis = [self._criar_nivel_default(NivelEnum.MT1)]
        with pytest.raises(ValueError, match="exatamente 5"):
            Poste(
                projeto_id=ProjetoId(),
                numero="P001",
                tipo_poste=TipoPoste.CONCRETO,
                niveis=niveis,
            )

    def test_poste_obter_nivel(self):
        """Poste can retrieve a specific Nivel by enum."""
        niveis = [self._criar_nivel_default(ne) for ne in NivelEnum]
        poste = Poste(
            projeto_id=ProjetoId(),
            numero="P001",
            tipo_poste=TipoPoste.CONCRETO,
            niveis=niveis,
        )
        mt1 = poste.obter_nivel(NivelEnum.MT1)
        assert mt1.nivel_enum == NivelEnum.MT1

    def test_poste_registrar_calculo(self):
        """Poste can register a calculation snapshot."""
        niveis = [self._criar_nivel_default(ne) for ne in NivelEnum]
        poste = Poste(
            projeto_id=ProjetoId(),
            numero="P001",
            tipo_poste=TipoPoste.CONCRETO,
            niveis=niveis,
        )
        resultado = CalculoResultado(
            mt1_tracao=100.0, mt1_angulo=5.0,
            mt2_tracao=0, mt2_angulo=0,
            bt_tracao=0, bt_angulo=0,
            btz_tracao=0, btz_angulo=0,
            ral_tracao=0, ral_angulo=0,
            total_tracao=100.0, total_angulo=5.0,
            poste_ecc=10.0,
        )
        snapshot = poste.registrar_calculo(resultado, "user1", "draft")
        assert snapshot.status == "draft"
        assert snapshot in poste.calculos

    def test_poste_marca_calculo_como_salvo(self):
        """Poste can mark draft calculation as saved."""
        niveis = [self._criar_nivel_default(ne) for ne in NivelEnum]
        poste = Poste(
            projeto_id=ProjetoId(),
            numero="P001",
            tipo_poste=TipoPoste.CONCRETO,
            niveis=niveis,
        )
        resultado = CalculoResultado(
            mt1_tracao=100.0, mt1_angulo=5.0,
            mt2_tracao=0, mt2_angulo=0,
            bt_tracao=0, bt_angulo=0,
            btz_tracao=0, btz_angulo=0,
            ral_tracao=0, ral_angulo=0,
            total_tracao=100.0, total_angulo=5.0,
            poste_ecc=10.0,
        )
        draft = poste.registrar_calculo(resultado, "user1")
        assert draft.status == "draft"
        
        salvo = poste.marcar_ultimo_calculo_como_salvo()
        assert salvo.status == "saved"

    def test_poste_obter_ultimo_calculo_salvo(self):
        """Poste can retrieve most recent saved calculation."""
        niveis = [self._criar_nivel_default(ne) for ne in NivelEnum]
        poste = Poste(
            projeto_id=ProjetoId(),
            numero="P001",
            tipo_poste=TipoPoste.CONCRETO,
            niveis=niveis,
        )
        # No calculations yet
        assert poste.obter_ultimo_calculo_salvo() is None
        
        # Register draft and save
        resultado = CalculoResultado(
            mt1_tracao=100.0, mt1_angulo=5.0,
            mt2_tracao=0, mt2_angulo=0,
            bt_tracao=0, bt_angulo=0,
            btz_tracao=0, btz_angulo=0,
            ral_tracao=0, ral_angulo=0,
            total_tracao=100.0, total_angulo=5.0,
            poste_ecc=10.0,
        )
        poste.registrar_calculo(resultado)
        salvo = poste.marcar_ultimo_calculo_como_salvo()
        
        # Should retrieve it
        retrieved = poste.obter_ultimo_calculo_salvo()
        assert retrieved is not None
        assert retrieved.id == salvo.id

    def test_poste_delete_soft(self):
        """Poste can be soft-deleted."""
        niveis = [self._criar_nivel_default(ne) for ne in NivelEnum]
        poste = Poste(
            projeto_id=ProjetoId(),
            numero="P001",
            tipo_poste=TipoPoste.CONCRETO,
            niveis=niveis,
        )
        assert not poste.esta_deletado()
        poste.deletar()
        assert poste.esta_deletado()


class TestNivelEntity:
    """Tests for Nivel entity (child of Poste aggregate)."""

    def test_nivel_rejeita_altura_poste_zero(self):
        """Nivel requires altura_poste > 0."""
        travessias = [
            Travessia(
                posicao=i,
                condutor=Condutor(
                    tipo_rede=TipoRede.CIRCUITO,
                    tipo_cabo=CaboConductor.CAA,
                    qtd_ligacoes=2,
                    qtd_cabos=3,
                ),
                geometria=Geometria(vao=15.0, flecha=0.5, angulo=10.0),
            )
            for i in range(1, 5)
        ]
        with pytest.raises(ValueError, match="Altura do poste"):
            Nivel(
                nivel_enum=NivelEnum.MT1,
                altura_poste=0,
                altura_ancoragem=0,
                travessias=travessias,
            )

    def test_nivel_rejeita_ancoragem_acima_do_poste(self):
        """Nivel rejects altura_ancoragem > altura_poste."""
        travessias = [
            Travessia(
                posicao=i,
                condutor=Condutor(
                    tipo_rede=TipoRede.CIRCUITO,
                    tipo_cabo=CaboConductor.CAA,
                    qtd_ligacoes=2,
                    qtd_cabos=3,
                ),
                geometria=Geometria(vao=15.0, flecha=0.5, angulo=10.0),
            )
            for i in range(1, 5)
        ]
        with pytest.raises(ValueError, match="não pode ser maior"):
            Nivel(
                nivel_enum=NivelEnum.MT1,
                altura_poste=11.0,
                altura_ancoragem=12.0,  # Taller than pole!
                travessias=travessias,
            )

    def test_nivel_rejeita_menos_de_4_travessias(self):
        """Nivel must have exactly 4 Travessias."""
        travessias = [
            Travessia(
                posicao=1,
                condutor=Condutor(
                    tipo_rede=TipoRede.CIRCUITO,
                    tipo_cabo=CaboConductor.CAA,
                    qtd_ligacoes=2,
                    qtd_cabos=3,
                ),
                geometria=Geometria(vao=15.0, flecha=0.5, angulo=10.0),
            )
        ]
        with pytest.raises(ValueError, match="exatamente 4"):
            Nivel(
                nivel_enum=NivelEnum.MT1,
                altura_poste=11.0,
                altura_ancoragem=9.0,
                travessias=travessias,
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
