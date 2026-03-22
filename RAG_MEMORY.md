# RAG_MEMORY - Memória de Trabalho do Agente

## 🚀 Stack Tecnológica (Enterprise Grade)
- **Frontend**: React (Vite), Tailwind CSS, Vitest.
- **Backend**: FastAPI (Python), SQLAlchemy, Alembic (Migrations), structlog.
- **Cache/RateLimit**: Redis.
- **Segurança**: Bandit (SAST), JWT Auth, CORS configurável.
- **Monitoramento**: Structured Logging, Deep Health Checks (/health/deep).
- **Infra**: Docker (Multi-stage build).

## 🏗️ Padrões Arquiteturais
- **Thin Frontend / Smart Backend**: Lógica pesada reside no backend (BudgetService, Calculo).
- **DDD (Domain-Driven Design)**: Repositórios, Serviços e Routers modularizados.
- **Resiliência**: Global Error Boundary e Rate Limiting.

## 🛡️ Segurança & Integridade
- **SQL Injection**: Protegido via parametrização e auditoria Bandit.
- **CI/CD Gates**: Bandit Scan e Coverage Gate (40% min) ativos no GitHub Actions.
- **Timeouts**: Configurados em 60s para chamadas de IA e 10s para conexões padrão.

## 📊 Métricas de Performance (Benchmarks)
- **RPS**: ~140 req/s em ambiente local.
- **Latência Média**: 67ms.
- **Rate Limit**: 100 req/min/IP em endpoints estruturais.

## 📜 Histórico de Ciclos
- **Ciclo 1**: Correção de fórmulas QDT e parity Excel.
- **Ciclo 2**: Refatoração BudgetService e Thin Frontend.
- **Ciclo 3**: Enterprise Elevation Phase 1 (Logging, Docker, Alembic).
- **Ciclo 4**: Enterprise Elevation Phase 2 (Security, Resiliency, Modularization).

---
*Mantenha esta memória atualizada para garantir continuidade entre sessões.*
