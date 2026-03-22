# ARCHITECTURE.md - Cálculo de Tração Light

## Visão Geral
Sistema especializado em engenharia elétrica para cálculo de tração de cabos e estruturas em redes aéreas, gerando relatórios normativos e plantas 2.5D.

## Stack Tecnológica
- **Frontend**: React (Vite), Tailwind CSS, Playwright (E2E)
- **Backend**: FastAPI (Python), SQLAlchemy, Alembic (Magrações), structlog (Logging)
- **Banco e Cache**: PostgreSQL (banco principal), Redis (cache)
- **Infra**: Docker (Multi-stage), Docker Compose

## Estrutura do Banco (Resumo)
- **Projeto**: Informações macro e metadados do projeto elétrico (ex. local, data).
- **Ponto** / **Tração**: Vértices/pontos de medição específicos no mapa e os resultados de forças calculadas neles.
- **Níveis e Travessias**: Detalhamento técnico dos condutores em cada nível (MT1, MT2, BT, BTZ, RAL).
- **Normas**: Regras da ABNT e parâmetros de validação para balizar os limites estruturais.

## Regras de Negócio & Engenharia
- A lógica de negócio e matemática (cálculos de tração e QDT) deve ser estritamente manuseada no Backend (Thin Frontend / Smart Backend).
- Qualquer cálculo estrutural deve respeitar estritamente as regras de limite das normas da concessionária vigentes (Zero erro / Enterprise Ready).
- **Observabilidade**: Todos os logs do backend são estruturados (JSON) via `structlog`.
- **Resiliência**: Global Exception Handler no backend e Error Boundaries no React.

## Estado Atual (Ponto de Parada)
- **Última Feature**: Elevação Enterprise concluída (Logging, Erros, Migrações, Boundaries, Docker Otimizado).
- **Métricas**: Benchmarks de 142 RPS e 100% de sucesso na API de Health Check.
- **Ticket Atual**: Manutenção e evolução contínua da arquitetura DDD.
