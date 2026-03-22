# Backlog Tecnico Frontend

## Premissas
- Excel/Workbook LIGHT continua como fonte de verdade funcional.
- Frontend permanece fino; sem mover regra de negocio para UI.
- Interface e mensagens em pt-BR.
- Estados de erro devem ser visiveis e acionaveis; nenhum fallback silencioso no fluxo critico.

## Status consolidado apos ciclo de hardening

### Concluido
- Validacao estrita de entrada em `buildNivelPayload` (sem coercao silenciosa para zero).
- Persistencia resiliente com retry/backoff (2s, 4s, 8s) e retry manual.
- Botao "Tentar novamente" para persistencia em erro.
- Acessibilidade base no formulario inicial e secoes tecnicas (labels, `aria-describedby`, `inputMode`).
- Ajustes de robustez backend para 422 de dominio e paridade BT Armado.

### Em aberto (Onda 2 UX operacional)
- Stepper operacional com loop ponto a ponto.
- Header com status duplo (vinculo e persistencia separados).
- APAGA com desfazer temporal (`UndoToast`).
- ActionBar fixa em mobile com area segura (`safe-area-inset-bottom`).

## Onda 2 - Tarefas por fluxo e componente

| ID | Fluxo | Componente | Tarefa tecnica | Arquivo alvo | Prioridade | Dependencia | Criterio de aceite |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FE-20 | Projeto -> Ponto -> Calculo | FlowStepper | Criar componente de 4 etapas (Projeto, Ponto, Calculo, Persistido) com estados `done`, `active`, `error` | src/components/fluxo/FlowStepper.jsx, src/App.jsx, src/index.css | Alta | Estado atual de fluxo no App | Stepper indica etapa atual sem ambiguidade; "Proximo ponto" aparece apenas apos persistencia `saved` |
| FE-21 | Ponto e Persistencia | HeaderStatusDuplo | Separar visualmente VinculoChip e PersistenciaChip com `aria-live=polite` em ambos | src/components/header/Header.jsx, src/App.jsx, src/index.css | Alta | FE-20 | Usuario identifica status de vinculo e status de gravacao como estados independentes |
| FE-22 | Ponto e Persistencia | PersistenciaChip | Fechar contrato de estados `saving`, `queued`, `saved`, `error_transient`, `error_permission` com mensagens e CTAs especificos | src/components/header/Header.jsx, src/hooks/usePersistenciaCalculo.js, src/index.css | Alta | FE-21 | Cada estado renderiza mensagem correta; countdown em `queued/error_transient` atualiza a cada 1s; CTA manual dispara `flushPersistQueue` sem bloquear formulario |
| FE-23 | Calculo tecnico | ActionBar | Implementar barra de acao contextual com CTA primario e CTA APAGA | src/components/acao/ActionBar.jsx, src/App.jsx, src/index.css | Alta | FE-20 | Desktop usa bloco lateral `sticky`; mobile usa barra fixa no rodape |
| FE-24 | Calculo tecnico | UndoToast | Fechar fluxo APAGA com desfazer em 5s incluindo mensagens, countdown e regra de foco | src/components/acao/UndoToast.jsx, src/App.jsx, src/index.css | Alta | FE-23 | APAGA abre `undo_pending` de 5s; CTA "Desfazer" restaura snapshot integral; foco vai para "Desfazer" ao abrir e retorna ao campo tecnico apos desfazer/timeout |
| FE-25 | Responsividade | Layout mobile | Ajustar `padding-bottom` do conteudo para ActionBar fixa + `env(safe-area-inset-bottom)` | src/index.css, src/App.jsx | Alta | FE-23 | Nenhum controle fica oculto atras da barra fixa em iOS/Android |
| FE-26 | Design system | Tokens | Aplicar snippet `theme.extend` da UX spec (surface/status/action/result/motion/tipografia) | tailwind.config.js | Media | Nenhuma | Tokens semanticos disponiveis sem quebrar tokens legados |
| FE-27 | QA funcional | E2E real | Criar suite E2E sem mocks para fluxo critico completo com backend real | e2e/ui-critical-flow-real.spec.js, playwright.config.js | Alta | Ambiente integrado disponivel | CI bloqueia merge se fluxo real falhar |
| FE-28 | QA mobile | Smoke fisico | Executar smoke em Android e iPhone para Stepper condensado, ActionBar fixa e APAGA com desfazer | docs/frontend-qa-checklist.md | Alta | FE-20..FE-25 | Evidencia registrada e sem bloqueio de usabilidade critica |
| FE-29 | Observabilidade UX | Instrumentacao | Instrumentar eventos `point_confirmed`, `calculation_persisted`, `persist_retry_manual`, `next_point_clicked` | src/App.jsx | Media | FE-20..FE-22 | Funil de task success e drop-off pode ser medido ponta a ponta |
| FE-30 | QA de release | Diagnostico estatico + regressao | Rodar diagnostico dos arquivos alterados e regressao Playwright critica | src/**/*, e2e/**/* | Alta | FE-20..FE-29 | Sem erros estaticos nos arquivos alterados e sem regressao E2E critica |
| FE-31 | Persistencia owner-only | Mensagem de autorizacao | Diferenciar UX de erro transiente vs erro `403/42501` na persistencia, bloqueando retry automatico para acesso negado e exibindo CTA de reconfirmacao | src/hooks/usePersistenciaCalculo.js, src/services/calculoApi.js, src/components/header/Header.jsx, src/App.jsx | Alta | Backend owner-only + FE-21 | Em `403/42501` nao ha retry automatico; mensagem explicita acesso/ownership; CTA "Reconfirmar projeto" fica disponivel |

## Definicao de pronto para lacunas criticas (gate de release)

APAGA + desfazer (5 s):

- Janela de desfazer dura 5 s com countdown visivel por segundo.
- Enquanto `undo_pending`, limpeza definitiva nao pode ocorrer.
- Desfazer restaura dados tecnicos do ponto atual sem afetar dados de projeto.
- Timeout sem desfazer aplica limpeza e posiciona foco no primeiro campo tecnico editavel.

Persistencia (estado e CTA):

- `saving`: sem CTA de retry e sem double-submit.
- `queued`: mostra "Na fila. Tentando em {N}s..." + CTA "Reenviar".
- `saved`: mostra "Salvo" + habilita "Proximo ponto".
- `error_transient`: mostra falha com retry automatico e CTA manual "Tentar novamente".
- `error_permission`: mostra acesso negado, sem retry automatico, com CTA "Reconfirmar projeto".

## Sequencia recomendada de execucao
1. FE-20 e FE-21 em paralelo (estrutura de fluxo + status duplo).
2. FE-22 e FE-23 em paralelo (persistencia visual + barra de acao).
3. FE-24 e FE-25 (desfazer APAGA + ajustes finais mobile).
4. FE-26 (tokens semanticos) e FE-29 (instrumentacao).
5. FE-27, FE-28, FE-30 e FE-31 para gate de release.

## Observacoes de implementacao
- Manter regra de ocultar `alturaPoste` e `alturaAncoragem` em T2, T3 e T4 por paridade workbook.
- Nao alterar ids de campos usados pelos testes E2E existentes.
- Nao introduzir logica de calculo nova no frontend.
