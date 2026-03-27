# Rastreabilidade e Evidências Operacionais — Template

**Arquivo:** `docs/analises/rastreabilidade-<data>-<responsavel>.md`  
**Propósito:** Registrar evidências de paridade LIGHT, trilha de rastreabilidade e classificação de erros críticos exigidos pelas seções 9 e 10 do `docs/frontend-qa-checklist.md`.

> **Instrução:** Copie este template, preencha cada seção com dados reais antes do merge para `main`, e assine ao final. Arquive o documento preenchido em `docs/analises/` com o nome `rastreabilidade-AAAA-MM-DD-<matricula>.md`.

---

## 1. Identificação da Operação de Teste

| Campo | Valor |
|-------|-------|
| Data | |
| Responsável (nome + matrícula) | |
| Ambiente | `staging` / `produção assistida` |
| Branch / commit SHA | |
| Versão frontend (package.json) | |
| Versão backend (tag ou commit) | |

---

## 2. Evidência de Paridade LIGHT (Gate 1)

Resultado do cálculo para o cenário representativo deve conter os mesmos valores que o workbook LIGHT para o mesmo conjunto de entradas.

### 2.1 Entradas usadas no cenário

```json
{
  "cabecalho": {
    "orgao": "",
    "ns": "",
    "projeto": "",
    "ponto": "",
    "tipo_poste": "",
    "modelo_poste": ""
  },
  "mt1": [{ "tipo_rede": "", "tipo_cabo": "", "vao": 0, "flecha": 0, "angulo": 0, "altura_poste": 0, "altura_ancoragem": 0 }],
  "bt": [],
  "btz": [],
  "ral": []
}
```

### 2.2 Resultado calculado pelo sistema

| Grandeza | Sistema | Workbook LIGHT | Δ | Dentro do critério? |
|----------|---------|----------------|---|----------------------|
| Tração total (daN) | | | | ☐ Sim ☐ Não |
| Ângulo total (°) | | | | ☐ Sim ☐ Não |
| Status do poste | | | | ☐ Sim ☐ Não |

**Critério de paridade adotado:** _(ex: diferença absoluta Δ ≤ 0.5 daN na tração resultante e Δ ≤ 0.5° no ângulo resultante — diferença absoluta entre o valor calculado pelo sistema e o valor da planilha LIGHT para as mesmas entradas)_

**Paridade aprovada?** ☐ Sim ☐ Não

---

## 3. Trilha de Rastreabilidade por Operação (Gate 2)

A trilha mínima é extraída dos eventos `[ux-funnel]` gerados pelo frontend (console ou callback).  
Cada linha deve conter: `timestamp | operation_id | evento | projeto_id | ponto_id | status`.

| ts (ISO 8601) | operation_id | evento | projeto_id | ponto_id | status_calculo | status_persistencia |
|---------------|-------------|--------|------------|----------|----------------|---------------------|
| | | project_confirmed | | — | — | — |
| | | point_confirmed | | | — | — |
| | | calculation_succeeded | | | OK | — |
| | | persistence_saved | | | OK | saved |

> **Como coletar:** Abra o DevTools Console durante a operação. Filtrar por `[ux-funnel]`.  
> Ou implemente `setUxFunnelEventCallback(handler)` para capturar em memória.

**Trilha completa disponível?** ☐ Sim ☐ Não  
**Localização do artefato:** _(ex: screenshot console em `docs/analises/evidencias/console-AAAA-MM-DD.png`)_

---

## 4. Classificação de Erros de Domínio Crítico (Gate 3)

Complete esta tabela apenas se algum erro 422 / 403 / 42501 ou divergência de paridade ocorreu.

| # | Erro | HTTP status | Causa identificada | Ação corretiva | Responsável | Data de resolução |
|---|------|-------------|-------------------|----------------|-------------|-------------------|
| 1 | | | | | | |

**Erros críticos sem mitigação?** ☐ Sim (bloquear merge) ☐ Não

---

## 5. Modo de Operação (Gate 4)

- [ ] Operação realizada em modo **assistido** com responsável técnico presente.
- [ ] Responsável técnico confirmou que todas as entradas estavam dentro do domínio operacional esperado.

**Nome do responsável técnico presente:** ______________________________

---

## 6. Decisão Go / No-Go (Gate 5)

| Campo | Valor |
|-------|-------|
| Aprovador | |
| Data da decisão | |
| Escopo liberado | |
| Pendências remanescentes | |
| Decisão | ☐ **Go** ☐ **No-Go** |

**Assinatura:** _____________________________ Data: ___________

---

## 7. Referências

- `docs/frontend-qa-checklist.md` — Seções 9 e 10
- `src/services/uxFunnelInstrumentation.js` — Eventos de rastreabilidade disponíveis
- `python/core/logging.py` — Logs de backend por operação
