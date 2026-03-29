"""Unit tests for Poste cross-project lineage.

Tests verify that:
1. vincular_origem() stores origem_id on the domain aggregate.
2. vincular_origem() raises on self-loop.
3. perfil() exposes origem_id when set.
4. perfil() exposes origem_id as None when not set.
5. PosteVincularIn validates UUID format.
6. LinhagemEntry / PosteLinhagem validate field types.
7. Service.vincular_origem() enforces cross-project business rules.
8. Service.obter_linhagem() raises ValueError for unknown Poste.
"""
import sys
import os

os.environ.setdefault("AUTH_REQUIRE_JWT_FOR_MUTATIONS", "false")
os.environ.setdefault("APP_ENV", "development")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from uuid import uuid4

from pydantic import ValidationError

from api.schemas import LinhagemEntry, PosteLinhagem, PosteVincularIn
from domain.aggregates import Poste
from domain.entities import Nivel, Travessia
from domain.value_objects import (
    CaboConductor,
    Condutor,
    Geometria,
    NivelEnum,
    PosteId,
    ProjetoId,
    TipoPoste,
    TipoRede,
)
from services.poste_service import PosteService


# ── Helpers ───────────────────────────────────────────────────────────────────

def _travessia(posicao: int) -> Travessia:
    return Travessia(
        posicao=posicao,
        condutor=Condutor(tipo_rede=TipoRede.CIRCUITO, tipo_cabo=CaboConductor.CAA),
        geometria=Geometria(vao=10.0, flecha=0.5, angulo=5.0),
    )


def _nivel(nivel_enum: NivelEnum) -> Nivel:
    return Nivel(
        nivel_enum=nivel_enum,
        altura_poste=11.0,
        altura_ancoragem=9.0,
        travessias=[_travessia(p) for p in range(1, 5)],
    )


def _poste(numero: str = "1", projeto_id: ProjetoId | None = None) -> Poste:
    return Poste(
        projeto_id=projeto_id or ProjetoId(),
        numero=numero,
        tipo_poste=TipoPoste.CONCRETO,
        modelo_poste="11/600",
        niveis=[_nivel(ne) for ne in NivelEnum],
    )


# ── Domain: vincular_origem() ─────────────────────────────────────────────────

class TestVincularOrigem:

    def test_vincular_sets_origem_id(self):
        poste = _poste()
        origem = PosteId()
        poste.vincular_origem(origem)
        assert poste.origem_id is not None
        assert poste.origem_id.value == origem.value

    def test_vincular_updates_atualizado_em(self):
        import time
        poste = _poste()
        before = poste.atualizado_em
        time.sleep(0.001)
        poste.vincular_origem(PosteId())
        assert poste.atualizado_em >= before

    def test_vincular_self_loop_raises(self):
        poste = _poste()
        with pytest.raises(ValueError, match="self-loop"):
            poste.vincular_origem(poste.id)

    def test_vincular_different_origem_ok(self):
        poste = _poste()
        other_id = PosteId()
        poste.vincular_origem(other_id)
        assert poste.origem_id.value == other_id.value


# ── Domain: perfil() now exposes origem_id ────────────────────────────────────

class TestPerfilComOrigem:

    def test_perfil_origem_none_when_not_linked(self):
        poste = _poste()
        assert poste.perfil()["origem_id"] is None

    def test_perfil_origem_present_when_linked(self):
        poste = _poste()
        origem = PosteId()
        poste.vincular_origem(origem)
        perfil = poste.perfil()
        assert perfil["origem_id"] == str(origem.value)


# ── API Schemas ───────────────────────────────────────────────────────────────

class TestPosteVincularIn:

    def test_valid_uuid_string_accepted(self):
        uid = str(uuid4())
        inp = PosteVincularIn(origem_id=uid)
        assert inp.origem_id == uid

    def test_empty_origem_id_rejected(self):
        with pytest.raises(ValidationError):
            PosteVincularIn(origem_id="")

    def test_missing_origem_id_rejected(self):
        with pytest.raises(ValidationError):
            PosteVincularIn()


class TestLinhagemEntry:

    def test_valid_entry(self):
        entry = LinhagemEntry(
            id=str(uuid4()),
            numero="3",
            tipo_poste="Concreto",
            modelo_poste="11/600",
            projeto_id=str(uuid4()),
        )
        assert entry.calculos_count == 0
        assert entry.origem_id is None

    def test_entry_with_all_fields(self):
        pid = str(uuid4())
        oid = str(uuid4())
        entry = LinhagemEntry(
            id=str(uuid4()),
            numero="3",
            tipo_poste="Concreto",
            modelo_poste="11/600",
            projeto_id=pid,
            origem_id=oid,
            atualizado_em="2026-01-01T00:00:00",
            calculos_count=5,
        )
        assert entry.origem_id == oid
        assert entry.calculos_count == 5


class TestPosteLinhagem:

    def test_valid_linhagem(self):
        entries = [
            LinhagemEntry(id=str(uuid4()), numero="7", tipo_poste="C", modelo_poste="11/600", projeto_id=str(uuid4())),
            LinhagemEntry(id=str(uuid4()), numero="5", tipo_poste="C", modelo_poste="11/600", projeto_id=str(uuid4())),
        ]
        linhagem = PosteLinhagem(
            poste_id=str(uuid4()),
            chain=entries,
            profundidade=2,
        )
        assert linhagem.profundidade == 2
        assert len(linhagem.chain) == 2


# ── Service layer (in-memory stub) ────────────────────────────────────────────

class _StubRepo:
    """Minimal in-memory stub for PosteRepository."""

    def __init__(self):
        self._postes: dict = {}
        self._linhagem_calls: list = []

    def obter_por_id(self, poste_id):
        return self._postes.get(str(poste_id))

    def obter_por_numero(self, projeto_id, numero):
        for p in self._postes.values():
            if p.projeto_id.value == projeto_id and p.numero == numero:
                return p
        return None

    def obter_todos_por_projeto(self, projeto_id):
        return [p for p in self._postes.values() if p.projeto_id.value == projeto_id]

    def salvar(self, poste):
        self._postes[str(poste.id.value)] = poste
        return poste

    def registrar_calculo(self, **kwargs):
        return uuid4()

    def obter_historico(self, poste_id):
        return []

    def deletar_suave(self, poste_id):
        pass

    def restaurar(self, poste_id):
        pass

    def vincular_origem(self, poste_id, origem_id):
        self._linhagem_calls.append((poste_id, origem_id))

    def obter_linhagem(self, poste_id, max_profundidade=50):
        return []


class TestPosteServiceLinhagem:

    def _build_service(self, *postes):
        repo = _StubRepo()
        for p in postes:
            repo._postes[str(p.id.value)] = p
        return PosteService(repo), repo

    def test_vincular_origem_same_project_raises(self):
        projeto = ProjetoId()
        p1 = _poste("1", projeto)
        p2 = _poste("2", projeto)
        svc, _ = self._build_service(p1, p2)
        with pytest.raises(ValueError, match="projetos diferentes"):
            svc.vincular_origem(p1.id.value, p2.id.value)

    def test_vincular_origem_different_projects_succeeds(self):
        p1 = _poste("1", ProjetoId())
        p2 = _poste("2", ProjetoId())
        svc, repo = self._build_service(p1, p2)
        svc.vincular_origem(p2.id.value, p1.id.value)
        # repo.vincular_origem was called
        assert len(repo._linhagem_calls) == 1
        assert repo._linhagem_calls[0] == (p2.id.value, p1.id.value)

    def test_vincular_origem_unknown_poste_raises(self):
        svc, _ = self._build_service()
        with pytest.raises(ValueError, match="não encontrado"):
            svc.vincular_origem(uuid4(), uuid4())

    def test_vincular_origem_unknown_origem_raises(self):
        p = _poste("1", ProjetoId())
        svc, _ = self._build_service(p)
        with pytest.raises(ValueError, match="não encontrado"):
            svc.vincular_origem(p.id.value, uuid4())

    def test_obter_linhagem_unknown_poste_raises(self):
        svc, _ = self._build_service()
        with pytest.raises(ValueError, match="não encontrado"):
            svc.obter_linhagem(uuid4())

    def test_obter_linhagem_existing_poste_returns_list(self):
        p = _poste("1", ProjetoId())
        svc, _ = self._build_service(p)
        result = svc.obter_linhagem(p.id.value)
        assert isinstance(result, list)


# ── Domain: clonar_para_projeto() ────────────────────────────────────────────

class TestClonarParaProjeto:

    def test_clone_is_new_aggregate(self):
        p = _poste("7", ProjetoId())
        destino = ProjetoId()
        clone = p.clonar_para_projeto(destino)
        assert clone.id.value != p.id.value, "clone must have a new UUID"
        assert clone.projeto_id.value == destino.value

    def test_clone_preserves_numero_and_structure(self):
        p = _poste("7", ProjetoId())
        destino = ProjetoId()
        clone = p.clonar_para_projeto(destino)
        assert clone.numero == "7"
        assert clone.tipo_poste == p.tipo_poste
        assert clone.modelo_poste == p.modelo_poste
        assert len(clone.niveis) == 5
        for n_orig, n_clone in zip(p.niveis, clone.niveis):
            assert n_clone.nivel_enum == n_orig.nivel_enum
            assert len(n_clone.travessias) == 4

    def test_clone_has_origem_id_set(self):
        p = _poste("7", ProjetoId())
        destino = ProjetoId()
        clone = p.clonar_para_projeto(destino)
        assert clone.origem_id is not None
        assert clone.origem_id.value == p.id.value

    def test_clone_modification_does_not_affect_original(self):
        p = _poste("7", ProjetoId())
        destino = ProjetoId()
        clone = p.clonar_para_projeto(destino)
        # Niveis in clone are separate objects (deepcopy), not the same instances
        assert clone.niveis[0] is not p.niveis[0]
        assert clone.niveis[0].travessias[0] is not p.niveis[0].travessias[0]
        # Geometria objects are immutable (frozen Pydantic) — independence is guaranteed
        # by the fact that clone niveis are different objects from origin niveis
        assert id(clone.niveis[0].travessias[0].geometria) != id(p.niveis[0].travessias[0].geometria)

    def test_clone_same_project_raises(self):
        projeto = ProjetoId()
        p = _poste("7", projeto)
        with pytest.raises(ValueError, match="projeto destino deve ser diferente"):
            p.clonar_para_projeto(projeto)

    def test_clone_passes_validar(self):
        p = _poste("7", ProjetoId())
        destino = ProjetoId()
        clone = p.clonar_para_projeto(destino)
        clone.validar()  # must not raise

    def test_clone_has_fresh_timestamp(self):
        import time
        p = _poste("7", ProjetoId())
        before = p.criado_em
        time.sleep(0.001)
        destino = ProjetoId()
        clone = p.clonar_para_projeto(destino)
        assert clone.criado_em >= before


# ── Service: clonar_para_projeto() ───────────────────────────────────────────

class _StubRepoClone(_StubRepo):
    """Extends _StubRepo with save tracking."""

    def salvar(self, poste):
        self._postes[str(poste.id.value)] = poste
        return poste


class TestPosteServiceClonar:

    def _build_service(self, *postes):
        repo = _StubRepoClone()
        for p in postes:
            repo._postes[str(p.id.value)] = p
        return PosteService(repo), repo

    def test_clone_same_project_raises(self):
        projeto = ProjetoId()
        p = _poste("1", projeto)
        svc, _ = self._build_service(p)
        with pytest.raises(ValueError, match="projeto destino deve ser diferente"):
            svc.clonar_para_projeto(p.id.value, projeto.value)

    def test_clone_unknown_origem_raises(self):
        svc, _ = self._build_service()
        with pytest.raises(ValueError, match="não encontrado"):
            svc.clonar_para_projeto(uuid4(), uuid4())

    def test_clone_creates_new_poste_in_repo(self):
        p = _poste("3", ProjetoId())
        destino = ProjetoId()
        svc, repo = self._build_service(p)
        clone = svc.clonar_para_projeto(p.id.value, destino.value)
        assert clone.id.value != p.id.value
        assert clone.projeto_id.value == destino.value
        assert clone.origem_id.value == p.id.value
        # Clone was saved in repo
        assert str(clone.id.value) in repo._postes

    def test_clone_inherits_numero(self):
        p = _poste("3", ProjetoId())
        destino = ProjetoId()
        svc, _ = self._build_service(p)
        clone = svc.clonar_para_projeto(p.id.value, destino.value)
        assert clone.numero == "3"

    def test_clone_deleted_origem_raises(self):
        p = _poste("1", ProjetoId())
        p.deletar()
        destino = ProjetoId()
        svc, _ = self._build_service(p)
        with pytest.raises(ValueError, match="deletado"):
            svc.clonar_para_projeto(p.id.value, destino.value)


# ── API: ClonarPosteIn schema ─────────────────────────────────────────────────

class TestClonarPosteIn:
    from api.schemas import ClonarPosteIn

    def test_valid_uuid_accepted(self):
        from api.schemas import ClonarPosteIn
        uid = str(uuid4())
        inp = ClonarPosteIn(projeto_id=uid)
        assert inp.projeto_id == uid

    def test_empty_projeto_id_rejected(self):
        from api.schemas import ClonarPosteIn
        with pytest.raises(ValidationError):
            ClonarPosteIn(projeto_id="")

    def test_missing_projeto_id_rejected(self):
        from api.schemas import ClonarPosteIn
        with pytest.raises(ValidationError):
            ClonarPosteIn()
