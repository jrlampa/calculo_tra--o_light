# ARCHITECTURE.md - Cálculo de Tração Light

## Visão Geral
Sistema especializado em engenharia elétrica para cálculo de tração de cabos e estruturas em redes aéreas, gerando relatórios normativos e plantas 2.5D.

## Stack Tecnológica
- **Frontend**: React (Vite), Tailwind CSS, Playwright (E2E)
- **Backend**: FastAPI (Python), SQLAlchemy, Ollama (IA Local)
- **Banco e Cache**: PostgreSQL (banco principal), Redis (cache)
- **Infra**: Docker, Docker Compose

## Estrutura do Banco (Resumo)
- **Projeto**: Informações macro e metadados do projeto elétrico (ex. local, data).
- **Poste**: Estruturas de suporte (tipo de material, resistência, altura).
- **Cabo**: Condutores elétricos que exercem tensão e peso na rede.
- **Ponto** / **Tração**: Vértices/pontos de medição específicos no mapa e os resultados de forças calculadas neles.
- **Normas**: Regras da ABNT e parâmetros de validação para balizar os limites estruturais.

## Regras de Negócio & Engenharia
- A lógica de negócio e matemática (cálculos de tração e QDT) deve ser estritamente manuseada no Backend e proibida no Frontend.
- Qualquer cálculo estrutural deve respeitar estritamente as regras de limite das normas da concessionária vigentes, impedindo falsos-positivos.
- É totalmente proibido o uso de dados mockados em qualquer etapa do fluxo.
- Sanitização obrigatória para garantir que medidas de tração (daN) possuam unidades e limites físicos autênticos.

## Estado Atual (Ponto de Parada)
- **Última Feature**: Refatoração da lógica de negócios e validação da paridade de UI 100% (cálculo de tração e remoção de componentes redundantes).
- **Ticket Atual**: Otimização rigorosa do consumo de contexto de agentes especialistas ("Guardião do Contexto do Sistema").
