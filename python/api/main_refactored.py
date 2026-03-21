"""FastAPI application – tração de poste calculator (Refatorado).

Run with:
    cd python
    uvicorn api.main_refactored:app --reload --port 8000

The React Vite dev server proxies /api/* to http://localhost:8000.
"""
from __future__ import annotations

import logging
import os
import sys
from typing import Optional

# Allow imports from the python/ directory when run as `uvicorn api.main:app`
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api.auth import (
    SESSION_COOKIE_NAME,
    SESSION_TTL_SECONDS,
    resolve_current_user,
)
from api.routers import calculo, projetos, public, admin
from db import get_supabase_client
from translated.plan1_tables import CABOS_POR_REDE, CABOS_TABLE, POSTE_TABLE, REDE_TABLE

app = FastAPI(title="Calculo Tração Poste", version="1.0.0")
logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase = get_supabase_client()


def _read_csv_env(var_name: str, default_csv: str) -> list[str]:
    """Lê variável de ambiente CSV e retorna lista de valores."""
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


# Health check
@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


# Config endpoint
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


# Incluir routers
app.include_router(calculo.router)
app.include_router(projetos.router)
app.include_router(public.router)
app.include_router(admin.router)
