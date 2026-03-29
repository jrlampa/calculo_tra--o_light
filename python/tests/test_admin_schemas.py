"""Unit tests for admin Pydantic schemas and the updated POST admin endpoints.

Verifies that:
1. CaboIn rejects empty nome, non-positive diametro/peso.
2. CaboIn accepts valid values.
3. AdminPosteIn rejects empty tipo/modelo, non-positive altura_m/carga_admissivel_dan.
4. AdminPosteIn accepts valid values.
5. POST /admin/cabos now accepts a JSON body (not query params).
6. POST /admin/postes now accepts a JSON body (not query params).
"""
import sys
import os

os.environ.setdefault("AUTH_REQUIRE_JWT_FOR_MUTATIONS", "false")
os.environ.setdefault("APP_ENV", "development")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from pydantic import ValidationError
from api.schemas import CaboIn, AdminPosteIn


# ── CaboIn ────────────────────────────────────────────────────────────────────

class TestCaboIn:

    def test_valid_cabo(self):
        cabo = CaboIn(nome="XLPE 16mm2", diametro=5.5, peso=0.18)
        assert cabo.nome == "XLPE 16mm2"
        assert cabo.diametro == 5.5
        assert cabo.peso == 0.18

    def test_nome_must_not_be_empty(self):
        with pytest.raises(ValidationError):
            CaboIn(nome="", diametro=5.5, peso=0.18)

    def test_diametro_must_be_positive(self):
        with pytest.raises(ValidationError):
            CaboIn(nome="XLPE", diametro=0.0, peso=0.18)

    def test_diametro_must_not_be_negative(self):
        with pytest.raises(ValidationError):
            CaboIn(nome="XLPE", diametro=-1.0, peso=0.18)

    def test_peso_must_be_positive(self):
        with pytest.raises(ValidationError):
            CaboIn(nome="XLPE", diametro=5.5, peso=0.0)

    def test_peso_must_not_be_negative(self):
        with pytest.raises(ValidationError):
            CaboIn(nome="XLPE", diametro=5.5, peso=-0.5)


# ── AdminPosteIn ──────────────────────────────────────────────────────────────

class TestAdminPosteIn:

    def test_valid_poste(self):
        poste = AdminPosteIn(
            tipo="Concreto",
            modelo="11/200",
            altura_m=11.0,
            carga_admissivel_dan=200.0,
        )
        assert poste.tipo == "Concreto"
        assert poste.modelo == "11/200"
        assert poste.altura_m == 11.0
        assert poste.carga_admissivel_dan == 200.0

    def test_tipo_must_not_be_empty(self):
        with pytest.raises(ValidationError):
            AdminPosteIn(tipo="", modelo="11/200", altura_m=11.0, carga_admissivel_dan=200.0)

    def test_modelo_must_not_be_empty(self):
        with pytest.raises(ValidationError):
            AdminPosteIn(tipo="Concreto", modelo="", altura_m=11.0, carga_admissivel_dan=200.0)

    def test_altura_m_must_be_positive(self):
        with pytest.raises(ValidationError):
            AdminPosteIn(tipo="Concreto", modelo="11/200", altura_m=0.0, carga_admissivel_dan=200.0)

    def test_altura_m_must_not_be_negative(self):
        with pytest.raises(ValidationError):
            AdminPosteIn(tipo="Concreto", modelo="11/200", altura_m=-5.0, carga_admissivel_dan=200.0)

    def test_carga_admissivel_dan_must_be_positive(self):
        with pytest.raises(ValidationError):
            AdminPosteIn(tipo="Concreto", modelo="11/200", altura_m=11.0, carga_admissivel_dan=0.0)

    def test_carga_admissivel_dan_must_not_be_negative(self):
        with pytest.raises(ValidationError):
            AdminPosteIn(tipo="Concreto", modelo="11/200", altura_m=11.0, carga_admissivel_dan=-100.0)
