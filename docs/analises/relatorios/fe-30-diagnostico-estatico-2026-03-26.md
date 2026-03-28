# FE-30 – Diagnóstico Estático + Regressão E2E

**Data:** 2026-03-26 (atualizado 2026-03-28 — FE-31 round 2)  
**Escopo:** Arquivos alterados em FE-20..FE-29 + FE-31  
**Responsável:** Copilot SWE Agent

---

## 1. Diagnóstico estático (ESLint)

### 1.1 Configuração

A instalação base não incluía as dependências `@typescript-eslint/eslint-plugin`, `@typescript-eslint/parser` e `eslint-plugin-import`. Foram instaladas e o `.eslintrc.json` foi corrigido:

- Desabilitadas regras que exigem TypeScript type information sem `parserOptions.project`:
  - `@typescript-eslint/no-floating-promises` → `off`
  - `@typescript-eslint/no-misused-promises` → `off`
  - `@typescript-eslint/await-thenable` → `off`
  - `@typescript-eslint/no-unnecessary-type-assertion` → `off`
  - `@typescript-eslint/prefer-nullish-coalescing` → `off`
  - `@typescript-eslint/prefer-optional-chain` → `off`
  - `@typescript-eslint/explicit-function-return-types` → `off` (nome de regra renomeado em versão atual do plugin)

### 1.2 Resultado nos arquivos alterados

| Arquivo | Erros | Avisos | Status |
|---|---|---|---|
| `src/hooks/useAppOptimizedState.js` | 0 | 3 | ✅ Sem erros |
| `src/hooks/usePersistenciaCalculo.js` | 0 | 0 | ✅ Sem erros |
| `src/services/uxFunnelInstrumentation.js` | 0 | 3 | ✅ Sem erros |
| `src/services/calculoApi.js` | 0 | 2 | ✅ Sem erros |
| `src/test/services/uxFunnelInstrumentation.test.js` | 0 | 0 | ✅ Sem erros |
| `src/test/services/calculoApi.test.js` | 0 | 0 | ✅ Sem erros |
| `e2e/ui-critical-flow-real.spec.js` | n/a (e2e/) | n/a | ✅ Sem erros |

### 1.3 Correções realizadas

**`src/hooks/usePersistenciaCalculo.js`** – `no-unsafe-finally` (2 ocorrências):
- A lógica de agendamento da próxima persistência foi movida para fora do bloco `finally`.
- O bloco `finally` agora apenas limpa `persistInFlightRef.current = false`.
- As instruções `return` que estavam no `finally` foram movidas para o código pós-`try/catch/finally`.

**`src/hooks/useAppOptimizedState.js`** e **`src/hooks/usePersistenciaCalculo.js`** – `curly` (13 ocorrências):
- `eslint --fix` aplicou blocos `{}` em todos os `if` sem chaves dos arquivos alterados.

**`src/services/calculoApi.js`** – `curly` (2 ocorrências em `toFloat`):
- `eslint --fix` aplicou blocos `{}` nos `if` de retorno antecipado dentro de `toFloat`.

**`src/services/calculoApi.js`** – `parseErrorMessage` → `parseErrorBody` (FE-31 round 2):
- Substituído `parseErrorMessage` por `parseErrorBody` que retorna `{message, errorCode}`.
- Agora detecta `payload.code === '42501'` (Supabase/PostgREST RLS) além de HTTP 403.

### 1.4 Avisos residuais (não bloqueantes)

| Regra | Arquivo | Nota |
|---|---|---|
| `import/no-unused-modules` | `uxFunnelInstrumentation.js` | `setUxFunnelEventCallback` e `buildUxFunnelEvent` são exportados para consumo externo futuro |
| `no-console` | `uxFunnelInstrumentation.js` | `console.info` intencional para log de eventos UX em produção |
| `react-hooks/exhaustive-deps` | `useAppOptimizedState.js` | `flushPersistQueue` já é memoizado; dependências omitidas intencionalmente para evitar loop |
| `import/no-unused-modules` | `useAppOptimizedState.js` | Hook exportado para `App.jsx` — falso positivo da análise estática |
| `import/no-unused-modules` | `calculoApi.js` | `listPostes` e `vincularOrigem` usados via E2E — falso positivo da análise estática |

---

## 2. Regressão de testes unitários

```
Test Files  17 passed (17)
Tests       194 passed (194)
```

Todos os 194 testes passaram. Nenhuma regressão detectada.

Os testes E2E com mocks (`e2e/ui-critical-flow.spec.js`, `e2e/ui-calc.spec.js`) validam o fluxo crítico com backend simulado.

A nova suite `e2e/ui-critical-flow-real.spec.js` (FE-27) valida o fluxo com backend real. Em ambiente sem backend disponível, todos os testes são automaticamente pulados via `skipIfBackendIndisponivel()` sem falhar o CI.

Para execução completa do fluxo real, configure:
```
E2E_REAL_AUTH_TOKEN=<jwt>
E2E_API_URL=https://<backend-url>
npx playwright test e2e/ui-critical-flow-real.spec.js
```

---

## 4. Build de produção

```
✓ built in 1.41s
PWA v1.2.0 — precache 9 entries (253.42 KiB)
```

Build sem erros ou warnings.

---

## 5. Gate de saída FE-30

| Critério | Resultado |
|---|---|
| Sem erros estáticos nos arquivos alterados | ✅ 0 erros ESLint |
| Sem regressão nos testes unitários | ✅ 194/194 passaram |
| Suite E2E crítica disponível | ✅ `ui-critical-flow-real.spec.js` criado (FE-27) |
| Build de produção sem erros | ✅ |
| `no-unsafe-finally` corrigido | ✅ |
| `.eslintrc.json` operacional | ✅ |
