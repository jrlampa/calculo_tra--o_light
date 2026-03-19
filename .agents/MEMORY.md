# Memory of Work - Projeto Cálculo de Tração Light

## 📌 Visão Geral
Sistema especializado para o cálculo de tração em postes de redes elétricas (Light), traduzindo lógica complexa de planilhas Excel (PLANILHA_DESTRAVADA.xlsm / AP COSMO LDA NOVA 03...) para uma aplicação web moderna com backend "inteligente" e frontend "magro".

## 🚀 Arquitetura Atual
- **Backend (Smart Backend)**: FastAPI (Python) estruturado seguindo princípios DDD.
  - Módulos principais: `excel_runtime`, `extract`, `translated`, `db`, `api`.
  - Integração com Supabase para persistência de dados (cabos, postes, redes, normas).
  - Cálculo de vetores e resultante em múltiplos níveis (MT, BT, Ramais).
- **Frontend (Thin Frontend)**: React + Vite + Tailwind CSS.
  - Componentes para visualização de relógio de ângulos, diagrama de poste e tabelas de carga.
  - Dashboard interativo sincronizado com os cálculos do backend em tempo real.

## 📊 Status do Desenvolvimento
- **Lógica de Cálculo**: Implementada no backend via `ponto_blocks.py`. Traduzida das regras do Excel.
- **UI/UX**: Refinamento de fidelidade em andamento para igualar as referências visuais do Excel.
- **Banco de Dados**: Configurado via Supabase, com suporte a fallback local para dados estáticos extraídos do Excel.
- **Testes**: Infraestrutura de E2E (Playwright) e testes unitários (Pytest) presente.
- **Docker**: Estrutura Docker configurada inicialmente (verificar localização de docker-compose).

## ⚠️ Regras e Restrições Ativas
- **Branch**: Apenas trabalhar na branch `dev`.
- **Coord para Teste**: 23K 788547 7634925 <-> 100m, -22.15018, -42.92185.
- **Visual**: Uso de 2.5D (não 3D).
- **Custo**: "Zero custo a todo custo!" (APIs públicas/gratuitas).
- **Idioma**: Interface em pt-BR.

## 🛠 Próximos Passos
1. Finalizar refinamento visual do frontend (Conversa c2841462).
2. Auditar fórmulas de queda de tensão (QDT) se necessário (Conversa 664cea88).
3. Verificar consistência do banco de dados no Supabase.
4. Garantir que os fluxos de trabalho (`/ciclo-*`) estejam operacionais na pasta `.agents/workflows`.

---
*Atualizado em: 19/03/2026*
