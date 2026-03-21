---
name: "UI Spec to React"
description: "Use when: convert UI spec to React components with Tailwind tokens, responsive behavior, accessibility, and implementation-ready handoff"
argument-hint: "Cole a especificacao de UI (ou descreva tela/fluxo), stack e restricoes de produto."
agent: "Product Designer Lead Senior"
tools: [read, search, edit]
---
Converta a especificacao visual fornecida em um pacote de implementacao para React.

Entregue exatamente:
1. Estrutura de componentes (TSX), separando UI e logica.
2. Mapeamento de props, estados e eventos por componente.
3. Snippet de tokens para `tailwind.config.js` em `theme.extend`.
4. Estrategia responsiva para Desktop, Tablet e Mobile.
5. Checklist de acessibilidade (WCAG 2.1 AA) aplicado ao layout.

Regras:
- Priorize Tailwind CSS e componentes funcionais.
- Use hooks customizados para logica de negocio.
- Inclua estados obrigatorios: loading, empty, error e success.
- Sempre justificar decisoes-chave com principios de UX/UI.

Formato de resposta:
- Secao "Arquitetura de Componentes"
- Secao "Contrato de Props e Estados"
- Secao "Tailwind Tokens"
- Secao "Plano Responsivo"
- Secao "Checklist A11y"
