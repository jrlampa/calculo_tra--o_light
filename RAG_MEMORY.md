# RAG_MEMORY - Memória de Trabalho do Agente

_Atualizado: 2026-03-22 | Ciclo: Enterprise Phase 4 Complete_

---

## 🚀 Stack Tecnológica (Enterprise Grade)

| Camada | Tecnologia |
|---|---|
| **Frontend** | React (Vite), Tailwind CSS, Vitest, Playwright (E2E) |
| **Backend** | FastAPI (Python), Pydantic v2, structlog, asyncpg |
| **Banco** | PostgreSQL (asyncpg), Alembic (migrations), Redis (cache/rate-limit) |
| **Segurança** | Bandit (SAST), JWT (PyJWT), CORS configurável, Rate Limiting |
| **Monitoramento** | Prometheus (/metrics), Deep Health Check (/health/deep), Sentry |
| **Infra** | Docker multi-stage, GitHub Actions CI/CD |

---

## 🏗️ Padrões Arquiteturais

- **Thin Frontend / Smart Backend**: Lógica de negócio reside no backend (cálculo vetorial, validações de engenharia).
- **DDD (Domain-Driven Design)**: Repositórios (`ProjetoRepository`), Serviços (`ProjetoService`), Routers modularizados (`/python/api/routers/`).
- **Resiliência**: Global Error Boundary (React), Rate Limiting (Redis), Graceful Degradation (Supabase indisponível → 503, não crash).

---

## 🗺️ Mapa de Rotas da API Enterprise

| Rota | Método | Auth | Descrição |
|---|---|---|---|
| `/health` | GET | Público | Status básico da API |
| `/health/deep` | GET | Público | Status detalhado (DB, Redis, Ollama) |
| `/metrics` | GET | Público | Prometheus metrics |
| `/api/calcular` | POST | Guest/JWT | Core engine de tração  |
| `/api/calcular/qdt` | POST | Guest/JWT | Cálculo de queda de tensão |
| `/api/cabos` | GET | Público | Lookup de cabos (tabela local) |
| `/api/postes` | GET | Público | Lookup de postes (tabela local) |
| `/api/redes` | GET | Público | Lookup de redes (tabela local) |
| `/api/normas` | GET | Público | Lookup de normas (Supabase) |
| `/api/public/normas/categorias` | GET | Público | Categorias de normas (Supabase) |
| `/api/config` | GET | Público | Configuração combinada (tabelas locais) |
| `/api/projetos` | GET/POST | JWT | CRUD projetos |
| `/api/projetos/{id}/pontos` | POST | JWT | Adicionar ponto ao projeto |
| `/api/pontos/{id}/calculo` | POST | JWT | Salvar snapshot do cálculo |
| `/api/admin/*` | * | Admin | Gerenciamento administrativo |
| `/api/monitoring/*` | GET | Auth | Métricas e alertas |
| `/api/cache/*` | * | Auth | Gestão de cache Redis |
| `/api/ai/*` | POST | JWT | Assistente IA (Ollama/LangChain) |

---

## 🔑 Padrões Críticos de Implementação

### Guest Mode (DX / Bypass JWT)
```python
# Backend: api/auth.py
# Header X-Guest-Access: true → bypassa JWT se import.meta.env.DEV === true
```
```javascript
// Frontend: src/hooks/useProjetoState.js
window.localStorage.setItem('guest_mode', 'true')  // chave CORRETA

// E2E Tests: e2e/*.spec.js
await page.addInitScript(() => {
  window.localStorage.setItem('guest_mode', 'true')  // NÃO usar 'guest_mode_confirmed'
})
```

### Dependency Injection (FastAPI)
```python
# CORRETO: sempre passar o callable como argumento para Depends()
async def meu_endpoint(supabase: object = Depends(get_supabase_dependency)):
    ...

# ERRADO: Depends() sem argumento retorna None no runtime
async def meu_endpoint(supabase: object = Depends()):  # BUG!
    ...
```

### Smoke Tests (Playwright API)
```javascript
// Supabase indisponível → 503 → test.skip (correto, não falha)
// Supabase OK → 200 → assertions normais
// Rotas lookup usam tabelas LOCAIS (CABOS_TABLE, REDE_TABLE, POSTE_TABLE)
// → não dependem de Supabase para responder!
```

### Rota do Core Engine (Validação Definitiva)
```bash
# Verificado manualmente em 2026-03-22:
curl -X POST http://127.0.0.1:8000/api/calcular \
  -H "Content-Type: application/json" \
  -d '{"cabecalho":{...}, "poste":{...}, ...}'
# → STATUS 200 OK, resposta com total_tracao_dan
```

---

## 📊 Métricas de Performance (Benchmarks)

- **RPS**: ~140 req/s em ambiente local (Locust).
- **Latência Média**: 67ms para `/api/calcular`.
- **Rate Limit**: 100 req/min/IP em endpoints estruturais.
- **Cobertura de Testes**: 46/46 unitários (100% backend Python).

---

## 🛡️ Segurança & Integridade

- **SQL Injection**: Protegido via asyncpg parametrizado (auditado por Bandit).
- **CI/CD Gates**: Bandit Scan + Coverage Gate (40% min) no GitHub Actions.
- **Timeouts**: 60s para chamadas de IA, 10s para conexões padrão.
- **Sanitização**: Dados de entrada validados por Pydantic v2 com construtores `model_validator`.

---

## ⚠️ Conhecimento & Gotchas

### Ambiente Local (Windows)
- **Virtual env**: `.venv` local tem dependências mínimas. Backend prod usa Python global do sistema.
- **Playwright reuseExistingServer**: `true` — NUNCA remover, evita timeout de 60s no startup.
- **`localhost` vs `127.0.0.1`**: Em alguns contextos Windows, `localhost` pode resolver IPv6. Usar `127.0.0.1` explícito nos smoke tests.
- **E2E_API_COMMAND**: Em Windows, usar `python` (não `python3`) e ativar env via `&&` inline.

### Supabase Fallback
- Endpoints de lookup (`/api/cabos`, `/api/postes`, `/api/redes`) respondem das **tabelas locais** (`plan1_tables.py`) e **NÃO dependem do Supabase**.
- Se Supabase estiver indisponível, esses endpoints DEVEM retornar **200** com dados locais.
- Somente `/api/normas` e `/api/projetos` requerem Supabase ativo.

### Cálculo Vetorial
- **Coordenadas de Teste**: `23K 788547 7634925 ↔ 100m`; `-22.15018, -42.92185 ↔ 500m & 1km`.
- **`modelo_poste`**: Campo obrigatório no payload `/api/calcular` para lookup de excentricidade.
- **`flecha > 0` quando `vao > 0`**: Validação de domínio no backend, reverte 422.

---

## 📜 Histórico de Ciclos

| Ciclo | Descrição | Status |
|---|---|---|
| 1 | Correção de fórmulas QDT e parity Excel | ✅ |
| 2 | Refatoração BudgetService e Thin Frontend | ✅ |
| 3 | Enterprise Elevation Phase 1 (Logging, Erros, Alembic) | ✅ |
| 4 | Enterprise Elevation Phase 2 (Segurança, Resiliência, Modularização DDD) | ✅ |
| 5 | Enterprise Elevation Phase 3 (Observabilidade, Prometheus, OpenAPI) | ✅ |
| 6 | Enterprise Phase 4 (PWA, Audit Trail, Guest DX, E2E Sync) | ✅ |
| 7 | Enterprise Final QA (Router DI fix, Smoke Tests, RAG Expansion) | ✅ |

---

*Mantenha esta memória atualizada para garantir continuidade entre sessões.*
