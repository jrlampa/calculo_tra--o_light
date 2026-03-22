# ARCHITECTURE.md - Cálculo de Tração Light

## Visão Geral

Sistema especializado em engenharia elétrica para cálculo de tração de cabos e estruturas em redes aéreas, gerando relatórios normativos e plantas 2.5D.

## Stack Tecnológica (Enterprise)
- **Frontend**: React (Vite), Tailwind CSS, Playwright (E2E)
- **Backend**: FastAPI (Python), SQLAlchemy, Alembic (Magrações), structlog (Logging)
- **Resiliência & Segurança**: Redis (Cache/RateLimit), Bandit (SAST), JWT Auth
- **Infra**: Docker (Multi-stage), Docker Compose

## 🏗️ Arquitetura Modular (DDD)

O backend é estruturado em domínios para garantir escalabilidade e separação de responsabilidades:
- **`api/main.py`**: Ponto de entrada enxuto, concentrando middlewares e monitoramento global.
- **`api/routers/`**: Routers especializados (`calculo`, `projetos`, `ai_assistant`, `monitoring`, `public`, `admin`).
- **`repositories/`**: Isolamento da camada de dados para fácil troca de drivers ou infraestrutura.
- **`services/`**: Orquestração da lógica de negócio e regras de engenharia.

## Estrutura do Banco (Resumo)

- **Projeto**: Informações macro e metadados do projeto elétrico (ex. local, data).
- **Ponto** / **Tração**: Vértices/pontos de medição específicos no mapa e os resultados de forças calculadas neles.
- **Níveis e Travessias**: Detalhamento técnico dos condutores em cada nível (MT1, MT2, BT, BTZ, RAL).
- **Normas**: Regras da ABNT e parâmetros de validação para balizar os limites estruturais.

## 🛡️ Regras de Negócio & Segurança

- **Thin Frontend / Smart Backend**: Lógica matemática estritamente no backend.
- **Zero custo a todo custo**: Uso prioritário de APIs gratuitas ou locais (Ollama).
- **Rate Limiting**: Proteção IP-based em endpoints estruturais via Redis.
- **Deep Health Check**: Monitoramento proativo em `/health/deep`.

## Estado Atual (Ponto de Parada)

- **Última Feature**: Elevação Enterprise Fase 2 concluída (Monitoramento Profundo, Rate Limit, Modularização DDD).
- **Métricas**: 100% Test Pass Rate (46+ testes). CI/CD com barreiras de Segurança e Cobertura.
- **Próximos Passos**: Observabilidade Avançada (Métricas Prometheus) e Auditoria A11y.
