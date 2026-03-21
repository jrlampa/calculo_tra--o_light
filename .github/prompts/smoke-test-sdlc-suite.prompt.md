---
name: "Smoke Test SDLC Suite"
description: "Use when: quick validation of SDLC Senior Engineer, Auto-Doc prompt, and Code Reviewer Security and Performance in 3 commands"
argument-hint: "Opcional: informe modulo/arquivos alvo para o teste rapido."
agent: "agent"
---
Gere um smoke test rapido das customizacoes deste workspace.

Retorne exatamente 3 comandos curtos, nesta ordem:
1. SDLC Senior Engineer
2. Auto-Doc
3. Code Reviewer Security and Performance

Regras:
- Responda somente com 3 linhas, sem explicacoes extras.
- Cada linha deve ser um comando pronto para colar no chat.
- Use caminhos reais do workspace quando possivel.
- Se o usuario nao informar arquivos, use defaults:
  - `python/api/main.py`
  - `src/App.jsx`

Objetivo dos 3 comandos:
- Comando 1 (SDLC): pedir proposta tecnica + pequeno plano de implementacao.
- Comando 2 (Auto-Doc): pedir README + OpenAPI + Mermaid para um arquivo/modulo.
- Comando 3 (Reviewer): pedir revisao estrita no formato [RISCO] | [LOCAL] | [MOTIVO] | [CORRECAO SUGERIDA].