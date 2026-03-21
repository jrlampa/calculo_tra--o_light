"""FastAPI application – tração de poste calculator.

Run with:
    cd python
    uvicorn api.main:app --reload --port 8000

The React Vite dev server proxies /api/* to http://localhost:8000.
"""
from __future__ import annotations

import logging
import math
import sys
import os
from typing import Optional

# Allow imports from the python/ directory when run as `uvicorn api.main:app`
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from db import get_supabase_client
from api.auth import (
    CurrentUser,
    SESSION_COOKIE_NAME,
    SESSION_TTL_SECONDS,
    get_current_user,
    require_admin,
    require_mutation_identity,
    resolve_current_user,
)

from api.schemas import (
    CalculoInput,
    CalculoOutput,
    LevelResultOut,
    VetorOut,
    QDTInput,
    QDTOutput,
    ProjetoIn,
    ProjetoOut,
    PontoIn,
    PontoOut,
    SalvarCalculoIn,
)
from translated.ponto_blocks import (
    BTTraversalInput,
    BTZeroTraversalInput,
    MTTraversalInput,
    RamaisTraversalInput,
    calcular_polo,
)
from translated.qdt_blocks import calcular_qdt, QDTInput as QDTLogicInput
from translated.plan1_tables import CABOS_POR_REDE, CABOS_TABLE, POSTE_TABLE, REDE_TABLE

app = FastAPI(title="Calculo Tração Poste", version="1.0.0")
logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase = get_supabase_client()


def _supabase_nao_configurado_exc() -> HTTPException:
    return HTTPException(
        status_code=503,
        detail="Supabase nao configurado. Defina DATABASE_URL no backend.",
    )


def _supabase_indisponivel_exc() -> HTTPException:
    logger.exception("Supabase indisponivel")
    return HTTPException(
        status_code=503,
        detail="Supabase indisponivel no momento. Tente novamente em instantes.",
    )


async def _ensure_supabase_available() -> None:
    if not supabase.is_enabled:
        raise _supabase_nao_configurado_exc()

    try:
        pool = await supabase._get_pool()
        if pool is None:
            raise RuntimeError("Pool do Supabase indisponivel")
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
    except HTTPException:
        raise
    except Exception:
        raise _supabase_indisponivel_exc()


async def _run_supabase_lookup(fetcher):
    await _ensure_supabase_available()
    try:
        return await fetcher()
    except Exception:
        raise _supabase_indisponivel_exc()


async def _fetch_cabos_lookup() -> list[dict]:
    return await _run_supabase_lookup(supabase.fetch_cabos)


async def _fetch_postes_lookup() -> list[dict]:
    return await _run_supabase_lookup(supabase.fetch_postes)


async def _fetch_redes_lookup() -> list[dict]:
    return await _run_supabase_lookup(supabase.fetch_redes)


async def _fetch_normas_lookup(categoria: Optional[str] = None) -> list[dict]:
    if categoria:
        return await _run_supabase_lookup(lambda: supabase.fetch_normas_by_categoria(categoria))
    return await _run_supabase_lookup(supabase.fetch_normas)


async def _fetch_normas_categorias_lookup() -> dict:
    return await _run_supabase_lookup(supabase.fetch_normas_categorias)


def _build_postes_por_tipo(postes: list[dict]) -> dict[str, list[str]]:
    postes_por_tipo: dict[str, list[str]] = {}
    for row in postes:
        tipo = row.get("tipo")
        modelo = row.get("modelo")
        if not tipo or not modelo:
            continue
        postes_por_tipo.setdefault(str(tipo), []).append(str(modelo))

    # Mantem ordem e remove duplicatas.
    return {tipo: list(dict.fromkeys(modelos)) for tipo, modelos in postes_por_tipo.items()}


def _read_csv_env(var_name: str, default_csv: str) -> list[str]:
    raw_value = os.getenv(var_name, default_csv)
    values = [value.strip() for value in raw_value.split(",")]
    return [value for value in values if value]


default_cors_origins = (
    "http://localhost:5173,"
    "http://localhost:3000,"
    "http://127.0.0.1:5173,"
    "http://127.0.0.1:3000"
)
default_cors_methods = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
default_cors_headers = "Authorization,Content-Type,X-Admin-Token,X-Request-Id"

app.add_middleware(
    CORSMiddleware,
    allow_origins=_read_csv_env("CORS_ALLOW_ORIGINS", default_cors_origins),
    allow_methods=_read_csv_env("CORS_ALLOW_METHODS", default_cors_methods),
    allow_headers=_read_csv_env("CORS_ALLOW_HEADERS", default_cors_headers),
    allow_credentials=True,
)


@app.middleware("http")
async def attach_current_user(request: Request, call_next):
    """Attach current user context from JWT or signed session for all requests."""
    resolved = resolve_current_user(request)
    request.state.current_user = resolved.current_user

    response = await call_next(request)

    if resolved.should_set_cookie and resolved.cookie_value:
        forwarded_proto = request.headers.get("x-forwarded-proto", "")
        is_secure = request.url.scheme == "https" or forwarded_proto.lower() == "https"
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=resolved.cookie_value,
            httponly=True,
            samesite="lax",
            max_age=SESSION_TTL_SECONDS,
            path="/",
            secure=is_secure,
        )

    return response


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/config")
async def get_config() -> dict:
    """Retorna opções de lookup a partir das tabelas traduzidas do workbook."""
    cabos_nomes = [str(row[0]) for row in CABOS_TABLE if row and row[0]]
    redes_nomes = [str(row[0]) for row in REDE_TABLE if row and row[0]]
    postes_por_tipo: dict[str, list[str]] = {
        str(tipo): [str(modelo[0]) for modelo in modelos if modelo and modelo[0]]
        for tipo, modelos in POSTE_TABLE.items()
    }

    return {
        "redes": redes_nomes,
        "cabos": cabos_nomes,
        "postes": postes_por_tipo,
        "cabos_por_rede": CABOS_POR_REDE,
    }


@app.post("/calcular/qdt", response_model=QDTOutput)
def calculate_qdt(inp: QDTInput) -> QDTOutput:
    """Run the Voltage Drop (QDT) calculation."""
    # Map Pydantic to Logic Input
    logic_in = QDTLogicInput(
        v_nominal_mt=inp.v_nominal_mt,
        v_nominal_bt=inp.v_nominal_bt,
        coef_perda=inp.coef_perda,
        reg_mt=inp.reg_mt,
        drop_mt_pct=inp.drop_mt_pct,
        drop_trafo_pct=inp.drop_trafo_pct,
        drop_bt1_pct=inp.drop_bt1_pct,
        drop_bt2_pct=inp.drop_bt2_pct,
    )
    res = calcular_qdt(logic_in)
    return QDTOutput(
        v_mt_initial=res.v_mt_initial,
        v_mt_node=res.v_mt_node,
        v_bt_start=res.v_bt_start,
        v_bt_node1=res.v_bt_node1,
        v_bt_node2=res.v_bt_node2,
        drop_total_pct=res.drop_total_pct,
    )


@app.post("/calcular", response_model=CalculoOutput)
def calcular(inp: CalculoInput) -> CalculoOutput:
    """Run the Ponto (1) calculation and return structured results."""
    # Convert Pydantic input to dataclasses used by ponto_blocks
    mt1 = [
        MTTraversalInput(
            tipo_rede=t.tipo_rede, tipo_cabo=t.tipo_cabo,
            vao=t.vao, flecha=t.flecha, angulo=t.angulo,
            altura_poste=t.altura_poste, altura_ancoragem=t.altura_ancoragem,
        )
        for t in inp.mt1
    ]
    mt2 = [
        MTTraversalInput(
            tipo_rede=t.tipo_rede, tipo_cabo=t.tipo_cabo,
            vao=t.vao, flecha=t.flecha, angulo=t.angulo,
            altura_poste=t.altura_poste, altura_ancoragem=t.altura_ancoragem,
        )
        for t in inp.mt2
    ]
    bt = [
        BTTraversalInput(
            tipo_rede=t.tipo_rede, tipo_cabo=t.tipo_cabo,
            vao=t.vao, flecha=t.flecha, angulo=t.angulo,
            altura_poste=t.altura_poste, altura_ancoragem=t.altura_ancoragem,
        )
        for t in inp.bt
    ]
    btz = [
        BTZeroTraversalInput(
            qtd_ligacoes=t.qtd_ligacoes,
            vao=t.vao, flecha=t.flecha, angulo=t.angulo,
            altura_poste=t.altura_poste, altura_ancoragem=t.altura_ancoragem,
        )
        for t in inp.btz
    ]
    ral = [
        RamaisTraversalInput(
            tipo_cabo=t.tipo_cabo, qtd_cabos=t.qtd_cabos,
            vao=t.vao, flecha=t.flecha, angulo=t.angulo,
            altura_poste=t.altura_poste, altura_ancoragem=t.altura_ancoragem,
        )
        for t in inp.ral
    ]

    try:
        result = calcular_polo(
            mt1_inputs=mt1,
            mt2_inputs=mt2,
            bt_inputs=bt,
            btz_inputs=btz,
            ral_inputs=ral,
            tipo_poste=inp.poste.tipo_poste,
            modelo_poste=inp.poste.modelo_poste,
        )

        # Build vector list for clock diagram
        level_defs = [
            ("MT1", result.mt1.f_tip, result.mt1.angulo),
            ("MT2", result.mt2.f_tip, result.mt2.angulo),
            ("BT",  result.bt.f_tip,  result.bt.angulo),
            ("BTZ", result.btz.f_tip, result.btz.angulo),
            ("RAL", result.ral.f_tip, result.ral.angulo),
        ]
        vetores = [
            VetorOut(
                label=label,
                tracao_dan=f,
                angulo_graus=a,
                comp_x=f * math.cos(a * math.pi / 180),
                comp_y=f * math.sin(a * math.pi / 180),
            )
            for label, f, a in level_defs
            if f != 0
        ]

        return CalculoOutput(
            mt1=LevelResultOut(
                tracao_dan=result.mt1.f_tip,
                angulo_graus=result.mt1.angulo,
                resultante_raw=result.mt1.resultante,
                texto=result.texto_mt1,
            ),
            mt2=LevelResultOut(
                tracao_dan=result.mt2.f_tip,
                angulo_graus=result.mt2.angulo,
                resultante_raw=result.mt2.resultante,
                texto=result.texto_mt2,
            ),
            bt=LevelResultOut(
                tracao_dan=result.bt.f_tip,
                angulo_graus=result.bt.angulo,
                resultante_raw=result.bt.resultante,
                texto=result.texto_bt,
            ),
            btz=LevelResultOut(
                tracao_dan=result.btz.f_tip,
                angulo_graus=result.btz.angulo,
                resultante_raw=result.btz.resultante,
                texto=result.texto_btz,
            ),
            ral=LevelResultOut(
                tracao_dan=result.ral.f_tip,
                angulo_graus=result.ral.angulo,
                resultante_raw=result.ral.resultante,
                texto=result.texto_ral,
            ),
            total_tracao_dan=result.total_tracao,
            total_angulo_graus=result.total_angulo,
            texto_total=result.texto_total,
            vetores=vetores,
            poste_ecc_dan=result.poste_ecc,
        )
    except (ValueError, ZeroDivisionError, ArithmeticError) as domain_err:
        logger.warning("Entrada inválida em /calcular: %s", domain_err)
        raise HTTPException(
            status_code=422,
            detail=f"Entrada fora do domínio operacional: {domain_err}",
        )
    except Exception:
        logger.exception("Erro interno durante /calcular")
        raise HTTPException(status_code=500, detail="Erro interno ao processar cálculo")


# ============================================================================
# Projetos / Pontos / Calculo — Endpoints de persistência
# ============================================================================

@app.get("/projetos", tags=["Projetos"])
async def list_projetos(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=10000),
    user: CurrentUser = Depends(require_mutation_identity),
) -> list:
    """Lista todos os projetos com contagem de pontos."""
    await _ensure_supabase_available()
    return await supabase.list_projetos(limit=limit, offset=offset, owner_id=user.user_id)


@app.post("/projetos", response_model=ProjetoOut, status_code=201, tags=["Projetos"])
async def create_projeto(
    inp: ProjetoIn,
    user: CurrentUser = Depends(require_mutation_identity),
) -> ProjetoOut:
    """Cria um novo projeto. Retorna o projeto com id gerado."""
    await _ensure_supabase_available()
    projeto_id = await supabase.save_projeto(
        {
            "orgao": inp.orgao,
            "ns": inp.ns,
            "nome": inp.nome,
            "endereco": inp.endereco,
            "estudado_por": inp.estudado_por,
            "matricula": inp.matricula,
            "data_estudo": inp.data_estudo,
        },
        owner_id=user.user_id,
    )
    if not projeto_id:
        raise HTTPException(status_code=500, detail="Erro ao salvar projeto")
    return ProjetoOut(
        id=projeto_id,
        orgao=inp.orgao,
        ns=inp.ns,
        nome=inp.nome,
        endereco=inp.endereco,
        estudado_por=inp.estudado_por,
        matricula=inp.matricula,
        data_estudo=inp.data_estudo,
        total_pontos=0,
    )


@app.post("/projetos/{projeto_id}/pontos", response_model=PontoOut, status_code=201, tags=["Projetos"])
async def create_ponto(
    projeto_id: str,
    inp: PontoIn,
    user: CurrentUser = Depends(require_mutation_identity),
) -> PontoOut:
    """Adiciona um novo ponto (poste) a um projeto existente."""
    await _ensure_supabase_available()

    can_access = await supabase.user_can_access_projeto(
        projeto_id=projeto_id,
        user_id=user.user_id,
    )
    if not can_access:
        raise HTTPException(status_code=403, detail="Sem permissão para este projeto")

    ponto_id = await supabase.save_ponto(
        projeto_id=projeto_id,
        ponto=inp.ponto,
        tipo_poste=inp.tipo_poste,
        modelo_poste=inp.modelo_poste,
    )
    if not ponto_id:
        raise HTTPException(
            status_code=409,
            detail=f"Ponto '{inp.ponto}' já existe neste projeto ou erro de persistência",
        )
    return PontoOut(
        id=ponto_id,
        projeto_id=projeto_id,
        ponto=inp.ponto,
        tipo_poste=inp.tipo_poste,
        modelo_poste=inp.modelo_poste,
    )


@app.post("/pontos/{ponto_id}/calculo", status_code=200, tags=["Projetos"])
async def salvar_calculo(
    ponto_id: str,
    inp: SalvarCalculoIn,
    user: CurrentUser = Depends(require_mutation_identity),
) -> dict:
    """Persiste travessias + resultado do cálculo para um ponto.

    Deve ser chamado logo após /calcular retornar com sucesso.
    Idempotente: reescreve completamente o estado salvo para esse ponto.
    """
    await _ensure_supabase_available()

    if str(inp.ponto_id) != ponto_id:
        raise HTTPException(status_code=422, detail="ponto_id do payload difere da rota")

    can_access = await supabase.user_can_access_ponto(
        ponto_id=ponto_id,
        user_id=user.user_id,
    )
    if not can_access:
        raise HTTPException(status_code=403, detail="Sem permissão para este ponto")

    ok_snapshot = await supabase.save_calculo_snapshot(
        ponto_id,
        [nivel.model_dump() for nivel in inp.niveis],
        inp.resultado.model_dump(),
    )
    if not ok_snapshot:
        raise HTTPException(status_code=500, detail="Erro ao persistir cálculo")
    return {"saved": True, "ponto_id": ponto_id}


# ============================================================================
# Admin Endpoints - Database Management
# ============================================================================

@app.get("/public/cabos", tags=["Publico"])
async def list_public_cabos():
    """Lista pública de cabos."""
    return await _fetch_cabos_lookup()


@app.get("/public/postes", tags=["Publico"])
async def list_public_postes():
    """Lista pública de postes."""
    return await _fetch_postes_lookup()


@app.get("/public/redes", tags=["Publico"])
async def list_public_redes():
    """Lista pública de redes."""
    return await _fetch_redes_lookup()


@app.get("/public/normas", tags=["Publico"])
async def list_public_normas(categoria: Optional[str] = None):
    """Lista pública de normas e regras."""
    return await _fetch_normas_lookup(categoria=categoria)


@app.get("/public/normas/categorias", tags=["Publico"])
async def list_public_normas_categorias():
    """Lista pública de categorias de normas."""
    return await _fetch_normas_categorias_lookup()


@app.get("/admin/cabos", tags=["Admin"])
async def list_admin_cabos(_: CurrentUser = Depends(require_admin)):
    """Lista administrativa de cabos."""
    return await _fetch_cabos_lookup()


@app.post("/admin/cabos", tags=["Admin"])
async def create_cabo(
    nome: str,
    diametro: float,
    peso: float,
    _: CurrentUser = Depends(require_admin),
):
    """Cria um novo cabo."""
    await _ensure_supabase_available()
    try:
        result = await supabase.insert_cabo(nome, diametro, peso)
    except Exception:
        raise _supabase_indisponivel_exc()

    if result == {}:
        raise HTTPException(status_code=500, detail="Falha ao criar cabo")

    return result


@app.delete("/admin/cabos/{cable_id}", tags=["Admin"])
async def delete_cabo(cable_id: int, _: CurrentUser = Depends(require_admin)):
    """Remove um cabo."""
    await _ensure_supabase_available()
    try:
        deleted = await supabase.delete_cabo(cable_id)
    except Exception:
        raise _supabase_indisponivel_exc()

    if not deleted:
        raise HTTPException(status_code=404, detail="Cabo nao encontrado para remocao")

    return {"success": True}


@app.get("/admin/postes", tags=["Admin"])
async def list_admin_postes(_: CurrentUser = Depends(require_admin)):
    """Lista administrativa de postes."""
    return await _fetch_postes_lookup()


@app.post("/admin/postes", tags=["Admin"])
async def create_poste(
    tipo: str,
    modelo: str,
    altura_m: float,
    carga_admissivel_dan: float,
    _: CurrentUser = Depends(require_admin),
):
    """Cria um novo poste."""
    await _ensure_supabase_available()
    try:
        result = await supabase.insert_poste(tipo, modelo, altura_m, carga_admissivel_dan)
    except Exception:
        raise _supabase_indisponivel_exc()

    if result == {}:
        raise HTTPException(status_code=500, detail="Falha ao criar poste")

    return result


@app.delete("/admin/postes/{poste_id}", tags=["Admin"])
async def delete_poste(poste_id: int, _: CurrentUser = Depends(require_admin)):
    """Remove um poste."""
    await _ensure_supabase_available()
    try:
        deleted = await supabase.delete_poste(poste_id)
    except Exception:
        raise _supabase_indisponivel_exc()

    if not deleted:
        raise HTTPException(status_code=404, detail="Poste nao encontrado para remocao")

    return {"success": True}


@app.get("/admin/redes", tags=["Admin"])
async def list_admin_redes(_: CurrentUser = Depends(require_admin)):
    """Lista administrativa de redes."""
    return await _fetch_redes_lookup()


@app.get("/admin/normas", tags=["Admin"])
async def list_admin_normas(
    categoria: Optional[str] = None,
    _: CurrentUser = Depends(require_admin),
):
    """Lista administrativa de normas e regras."""
    return await _fetch_normas_lookup(categoria=categoria)


@app.get("/admin/normas/categorias", tags=["Admin"])
async def list_admin_normas_categorias(_: CurrentUser = Depends(require_admin)):
    """Lista administrativa de categorias de normas."""
    return await _fetch_normas_categorias_lookup()
