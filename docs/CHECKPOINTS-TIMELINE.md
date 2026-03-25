# CHECKPOINTS TIMELINE (PM) - D+2 / D+5 / D+7

## 1) Resumo executivo e decisão atual

A convergência técnica avançou em planejamento e trilho de execução, com backlog crítico
já estruturado por agente e checkpoints definidos em 48h, D+5 e D+7.

Decisão atual: No-Go condicionado até fechar contrato/auth/snapshot no fluxo crítico
Projeto -> Ponto -> Persistido -> Snapshot, com evidência objetiva e gate operacional ativo.

Premissas ativas para decisão:

- Excel LIGHT permanece fonte de verdade para paridade de cálculo.
- Liberação segue bloqueada quando houver critério crítico em estado release_blocked.
- Go/No-Go depende de evidências testáveis, não apenas parecer textual.

## 2) D+2 (48h) executado

- SDLC
  - Status D+2: Concluído (plano/evidência inicial).
  - Bloqueadores principais: falta consolidar quality gates completos
    (unit, e2e crítico, security, schema-check).
  - Decisão parcial: manter execução com bloqueio de release até fechamento
    dos gates obrigatórios.

- DBA
  - Status D+2: Em andamento (execução).
  - Bloqueadores principais: contrato de persistência/snapshot ainda não formalizado
    ponta a ponta; governança de migração/schema precisa convergir.
  - Decisão parcial: sem Go parcial para persistência enquanto contrato e consistência
    de migração não estiverem comprovados.

- Security + Performance (C1/C2/C3 + gate)
  - Status D+2: Em andamento (execução).
  - Bloqueadores principais: C1 segredos por ambiente; C2 serialização segura no cache;
    C3 gate de segurança no CI ainda pendente de fechamento completo.
  - Decisão parcial: risco operacional ainda aberto; manter No-Go condicionado.

- Product + UX (KPIs + rollout)
  - Status D+2: Concluído (plano/evidência inicial).
  - Bloqueadores principais: dependência de estabilidade de contrato/auth/snapshot para
    validar KPIs de confiança em ambiente real.
  - Decisão parcial: rollout permanece faseado, sem expansão do fluxo crítico
    até convergência técnica.

- Engenharia Normas
  - Status D+2: Concluído (plano/evidência inicial).
  - Bloqueadores principais: checklist técnico de conformidade Go/No-Go ainda depende
    de evidências finais de paridade/rastreabilidade.
  - Decisão parcial: gate normativo permanece bloqueante até comprovação objetiva.

## 3) D+5: checklist Must have

- Backlog Sprint 1 crítico operacional
  - Dono: SDLC.
  - Critério objetivo: tasks críticas com owner, prazo e aceite testável;
    status atualizado por checkpoint.
  - Evidência esperada: ata D+5 com status por task e risco residual por agente.

- Contrato de persistência + snapshot formalizado
  - Dono: DBA.
  - Critério objetivo: contrato de rota e semântica 200/404/403 definido e testado
    no fluxo crítico.
  - Evidência esperada: documento de contrato + teste automatizado passando para
    escrita/leitura de snapshot.

- C1/C2/C3 de segurança com gate ativo
  - Dono: Security + Performance.
  - Critério objetivo: C1 segredos sem hardcode; C2 sem desserialização insegura
    no caminho crítico; C3 scan de segurança bloqueando merge quando falhar.
  - Evidência esperada: evidência de CI com etapa de security scan ativa +
    validação técnica de cache seguro.

- KPIs de confiança e plano de rollout em etapas
  - Dono: Product + UX.
  - Critério objetivo: KPIs operacionais definidos e instrumentação mínima ativa
    para checkpoint.
  - Evidência esperada: lista de eventos de governança/confiabilidade registrada +
    plano de rollout/rollback.

- Checklist normativo Go/No-Go atualizado
  - Dono: Engenharia Normas.
  - Critério objetivo: checklist de conformidade e gates de paridade/rastreabilidade
    aplicáveis ao release.
  - Evidência esperada: checklist preenchível com critérios de aprovação/reprovação e
    vínculo a evidências.

## 4) D+7: decisão parcial Go/No-Go (critérios objetivos)

Decisão parcial esperada em D+7:

- Go parcial somente se todos os critérios abaixo forem atendidos simultaneamente.
- No-Go se qualquer critério crítico falhar.

Critérios objetivos por eixo:

- Contrato:
  - Rotas críticas sem 404 estrutural em E2E do fluxo crítico.
  - Contrato de escrita/leitura documentado e validado por teste.
- Auth:
  - Semântica consistente para 401/403 em endpoints críticos.
  - Política de autenticação de escrita padronizada no ambiente de validação.
- Snapshot:
  - Snapshot retorna 200 quando presente e 404 apenas quando realmente ausente.
  - Fluxo Projeto -> Ponto -> Persistido -> Snapshot validado com evidência auditável.

Regra de decisão D+7:

- Go parcial: contrato/auth/snapshot com aceite objetivo + gate sem bloqueio crítico.
- No-Go: qualquer falha em contrato/auth/snapshot ou ausência de evidência objetiva.

## 5) Riscos residuais

- Divergência de contrato entre API/E2E no fluxo crítico
  - Impacto: Alto.
  - Probabilidade: Médio.
  - Mitigação ativa: normalização de contrato e validação automatizada em checkpoint.
  - Owner: SDLC + DBA.

- Falha de autenticação/autorização sem semântica única
  - Impacto: Alto.
  - Probabilidade: Médio.
  - Mitigação ativa: padronização 401/403 e gate de validação antes de release.
  - Owner: Security + Performance.

- Snapshot ausente/inconsistente após persistência
  - Impacto: Alto.
  - Probabilidade: Médio.
  - Mitigação ativa: teste ponta a ponta escrita+leitura e bloqueio de avanço
    sem confiança operacional.
  - Owner: DBA + Product + UX.

- Liberação sem evidência normativa suficiente
  - Impacto: Alto.
  - Probabilidade: Baixo/Médio.
  - Mitigação ativa: aplicação dos gates de paridade e rastreabilidade com
    decisão formal registrada.
  - Owner: Engenharia Normas.

## 6) Próximas ações

- D+2
  - Ação: consolidar status real por agente no template único de checkpoint.
  - Responsável: SDLC (orquestração).
  - Resultado esperado: painel de convergência atualizado com bloqueadores explícitos.

- D+2
  - Ação: publicar versão consolidada de critérios contrato/auth/snapshot para
    validação cruzada.
  - Responsável: DBA + Security + Product/UX.
  - Resultado esperado: critérios únicos sem ambiguidade para execução D+5.

- D+5
  - Ação: fechar execução Must have com evidências anexadas por critério.
  - Responsável: todos os donos de trilha.
  - Resultado esperado: pacote de evidências pronto para decisão parcial.

- D+5
  - Ação: rodar validação de gate operacional (paridade, rastreabilidade,
    domínio crítico).
  - Responsável: Engenharia Normas + QA/SDLC.
  - Resultado esperado: parecer técnico objetivo para decisão D+7.

- D+7
  - Ação: emitir decisão parcial Go/No-Go e registrar pendências/rollback.
  - Responsável: PM + Tech Lead + responsáveis de trilha.
  - Resultado esperado: ata de decisão com escopo liberado, riscos residuais e
    próximos passos.

## 7) Critério de encerramento

O ciclo de checkpoint será encerrado quando todos os itens abaixo estiverem atendidos:

- Decisão D+7 formalmente registrada (Go parcial ou No-Go) com aprovadores e pendências.
- Contrato/auth/snapshot fechados com evidência objetiva no fluxo crítico.
- Gate normativo e gate operacional sem bloqueio crítico aberto para o escopo avaliado.
- Plano de continuidade (rollout assistido ou remediação) definido com responsáveis e
  nova janela de checkpoint.
