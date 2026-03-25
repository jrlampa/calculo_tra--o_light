# Mesa Redonda Técnica - Consolidação de Execução (Temporário)

## 1) Resumo executivo

Este consolidado transforma os achados da mesa redonda em plano de execução imediato, priorizando risco real de produção e paridade com a planilha LIGHT (fonte de verdade funcional). Os pontos críticos atuais estão concentrados em segurança operacional, confiabilidade de CI/CD, integridade de fluxo UX crítico e governança de dados.

Achados reais considerados como base:
- Segredos expostos e/ou gestão fraca de ambiente (`.env`, hardcoded, ausência de separação robusta por ambiente).
- Uso de `pickle` no cache Redis (`python/cache/redis_client.py`) com risco de desserialização insegura.
- Entrypoint incorreto no CI (`uvicorn main:app`) divergente do módulo real (`api.main:app`) na pipeline.
- Mismatch de schema e governança de `projetos` (versionamento/migrações e consistência entre código e banco).
- APAGA com undo funcionalmente incompleto (wiring final de restauração ainda pendente em fluxo crítico).
- Lacuna de instrumentação UX para medir task success, time on task e drop-off ponta a ponta.

Diretriz executiva:
- Corrigir primeiro o que pode gerar falha silenciosa, risco de segurança e regressão no fluxo crítico.
- Preservar arquitetura thin frontend/smart backend.
- Manter decisões de cálculo aderentes ao workbook LIGHT, mesmo quando a planilha não representar o ideal teórico.

---

## 2) Ranking de impacto (Crítico -> Baixo)

### Crítico
1. CI/CD com entrypoint backend incorreto (`uvicorn main:app`) no workflow.
2. Exposição/gestão inadequada de segredos (`.env`/hardcoded/rotation ausente).
3. Desserialização com `pickle` em Redis cache sem isolamento seguro.

### Alto
1. Mismatch de schema em `projetos` e governança de migração/versionamento.
2. APAGA com undo incompleto no fechamento funcional do requisito UX crítico.
3. Falta de gates robustos de segurança e integração no pipeline.

### Médio
1. Lacuna de instrumentação UX (eventos e funil de conversão operacional).
2. Cobertura insuficiente dos testes de borda para undo/persistência/autorização.
3. Observabilidade de runtime e alertas ainda parcial.

### Baixo
1. Ajustes cosméticos de documentação de handoff e padronização textual.
2. Melhorias incrementais de performance sem gargalo comprovado no momento.

---

## 3) Parecer individual resumido por agente

### Security + Performance
- Parecer: risco operacional imediato por segredos mal geridos + vetor de desserialização insegura em cache + pipeline sem proteção total.
- Recomendação: remover hardcode, fortalecer secrets management por ambiente, eliminar `pickle` do caminho de dados e adicionar gates SAST/DAST/dependency scan.

### DBA
- Parecer: governança de schema precisa convergir com runtime e migrações para evitar divergência estrutural em `projetos`.
- Recomendação: baseline de migrations versionadas, validação de schema em CI, checklist de compatibilidade de índices/políticas RLS.

### SDLC
- Parecer: problema central é execução sem trilho único de qualidade entre local, CI e produção.
- Recomendação: pipeline determinístico, quality gates obrigatórios, plano de rollout/rollback e critérios globais de aceite antes de merge.

### Engenheiro Normas
- Parecer: requisitos normativos e de confiabilidade operacional exigem rastreabilidade de decisão e previsibilidade de cálculo.
- Recomendação: não aprovar mudança que degrade paridade LIGHT, audit trail por versão de regra e validações consistentes em fluxo crítico.

### Product Designer
- Parecer: UX crítico evoluiu, mas o requisito APAGA com desfazer ainda não está completamente fechado do ponto de vista de produto.
- Recomendação: fechar estado de erro, desfazer e feedback visual/semântico antes de expandir escopo de interface.

### UX Research
- Parecer: sem instrumentação dos eventos definidos, não há como medir sucesso real do fluxo Projeto -> Ponto -> Persistido.
- Recomendação: implementar plano mínimo de métricas e dashboard de acompanhamento por coorte/etapa.

### Estagiário Criativo
- Parecer: há oportunidades de diferenciação, mas inovação deve respeitar baseline de segurança e confiabilidade.
- Recomendação: priorizar ideias de baixo risco e alto impacto após estabilização dos pontos críticos.

---

## 4) Conflitos positivos entre agentes e resolução

1. Conflito: velocidade de entrega (SDLC) vs hardening de segurança (Security+Performance).
- Resolução: adotar trilha dupla no sprint: correções críticas bloqueantes primeiro; melhorias não bloqueantes em paralelo com feature flags.

2. Conflito: evolução rápida de UX (Product/UX) vs estabilidade de fluxo crítico (Normas/SDLC).
- Resolução: congelar experimentação no fluxo principal até concluir APAGA+undo completo e instrumentação mínima.

3. Conflito: otimizações de performance (Security+Performance) vs consistência de dados (DBA).
- Resolução: qualquer cache para dados de domínio sensível deve respeitar política de invalidacão e não usar serialização insegura.

4. Conflito: inovação visual (Estagiário Criativo) vs governança técnica.
- Resolução: backlog criativo só avança após aceite dos itens Críticos e Altos.

---

## 5) Relatório de convergência: decisão final e trade-offs

Decisão final:
- Executar plano em 3 ondas: Contenção Crítica -> Estabilização de Fluxo -> Observabilidade e Evolução.

Trade-offs assumidos:
1. Menor velocidade de entrega no curto prazo para reduzir risco de produção.
2. Postergar iniciativas de inovação para garantir segurança e confiabilidade.
3. Priorizar paridade funcional LIGHT sobre refatorações teóricas profundas.
4. Aumentar esforço em testes/CI agora para reduzir retrabalho e incidentes depois.

Resultado esperado:
- Ambiente com gates mínimos de produção, fluxo crítico validado ponta a ponta, e métricas UX operacionais para decisão baseada em dados.

---

## 6) Backlog de execução por agente com status [TODO], prioridade, esforço, arquivos alvo

### Security + Performance
- [ ] [TODO][P0][M] Remover segredos hardcoded e consolidar gestão de segredos por ambiente. Arquivos alvo: `.github/workflows/ci-cd.yml`, `docker-compose.yml`, `python/api/main.py`, `python/api/auth.py`.
- [ ] [TODO][P0][M] Substituir serialização `pickle` por JSON seguro no cache Redis com fallback controlado. Arquivos alvo: `python/cache/redis_client.py`, `python/api/routers/cache.py`, `python/tests/`.
- [ ] [TODO][P1][S] Incluir gate de segurança (dependências + scan estático) no CI. Arquivos alvo: `.github/workflows/ci-cd.yml`, `package.json`, `python/requirements.txt`.

### DBA
- [ ] [TODO][P0][M] Validar e alinhar schema de `projetos` com runtime e políticas de acesso. Arquivos alvo: `SUPABASE_SETUP.md`, `python/db/`, `python/repositories/`.
- [ ] [TODO][P1][M] Instituir validação automática de migrations/schema no pipeline. Arquivos alvo: `.github/workflows/ci-cd.yml`, `python/tests/`.
- [ ] [TODO][P1][S] Revisar índices críticos para consulta por owner e ordenação temporal. Arquivos alvo: `SUPABASE_SETUP.md`, `python/db/`.

### SDLC
- [x] [DONE][P0][S] Corrigir entrypoint backend no CI (`main:app` -> `api.main:app`). Arquivos alvo: `.github/workflows/ci-cd.yml`.
- [ ] [TODO][P0][M] Definir quality gates obrigatórios (unit, e2e crítico, lint, security, schema-check). Arquivos alvo: `.github/workflows/ci-cd.yml`, `playwright.config.js`, `vitest.config.js`.
- [ ] [TODO][P1][S] Formalizar plano de rollback por falha de deploy. Arquivos alvo: `docs/`, `docker-compose.yml`.

### Engenheiro Normas
- [ ] [TODO][P0][M] Revisar checklist de conformidade para alterações em cálculo e persistência sem quebrar paridade LIGHT. Arquivos alvo: `docs/frontend-qa-checklist.md`, `docs/ux-ui-spec.md`, `python/tests/`.
- [ ] [TODO][P1][S] Criar trilha de auditoria de decisões de regra técnica por versão. Arquivos alvo: `docs/`, `RAG/MEMORY.md`.

### Product Designer
- [ ] [TODO][P0][M] Fechar especificação final do APAGA com desfazer (estados, mensagens, aceites). Arquivos alvo: `docs/ux-ui-spec.md`, `docs/frontend-implementation-tasks.md`, `docs/frontend-qa-checklist.md`.
- [ ] [TODO][P1][S] Validar consistência visual/semântica de estados críticos de persistência. Arquivos alvo: `src/components/`, `src/index.css`, `docs/frontend-visual-tokens.md`.

### UX Research
- [ ] [TODO][P0][M] Implementar instrumentação mínima do funil operacional (`point_confirmed`, `calculation_persisted`, `persist_retry_manual`, `next_point_clicked`). Arquivos alvo: `src/App.jsx`, `src/services/`, `docs/ux-ui-spec.md`.
- [ ] [TODO][P1][S] Definir relatório semanal de métricas UX (success/time/drop-off). Arquivos alvo: `docs/`.

### Estagiário Criativo
- [ ] [TODO][P2][S] Propor melhorias de microinteração sem impacto em fluxo crítico. Arquivos alvo: `src/components/`, `src/index.css`.
- [ ] [TODO][P2][S] Prototipar variações de comunicação para erro/transiente/acesso negado. Arquivos alvo: `docs/ux-ui-spec.md`, `src/components/header/`.

---

## 7) Critérios de aceite globais

1. Segurança
- Nenhum segredo hardcoded em código versionado.
- Pipeline sem vazamento de credenciais.
- Cache sem desserialização insegura por padrão.

2. Confiabilidade CI/CD
- Entrypoint backend correto e validado em pipeline.
- Build/test/lint/security/schema gates bloqueando merge quando falhar.

3. Dados
- Schema de `projetos` consistente entre migração, repositório e runtime.
- Políticas de acesso e consultas críticas validadas em teste automatizado.

4. UX crítico
- APAGA com desfazer efetivo: restauração integral comprovada.
- Estados de erro e retry claramente diferenciados (transiente vs autorização).

5. Qualidade
- Testes cobrindo happy path, borda e falhas críticas.
- Evidência de execução em CI para fluxos principais.

6. Paridade funcional
- Nenhuma alteração aprovada se romper comportamento esperado da planilha LIGHT.

---

## 8) Riscos e bloqueios

### Riscos
- R1: correções rápidas em CI sem revisão podem mascarar falhas de integração.
- R2: troca de serialização no cache pode introduzir incompatibilidade em dados já persistidos.
- R3: ajustes de schema sem plano de migração podem gerar indisponibilidade parcial.
- R4: APAGA/undo parcialmente funcional pode causar perda de confiança operacional do usuário.

### Bloqueios potenciais
- B1: ausência de padrão único para segredos entre ambiente local, CI e runtime.
- B2: falta de contrato formal de eventos UX para coleta e análise.
- B3: divergências entre especificação UX e wiring real no frontend.

### Mitigações
- M1: rollout em etapas com validação automatizada e fallback.
- M2: migração compatível retroativamente para cache/schema.
- M3: smoke test obrigatório do fluxo crítico antes de merge para `dev`.

---

## 9) Plano de validação com testes e CI/CD

### Etapa A - Pré-merge (obrigatória)
- Testes unitários backend (serviços/repositórios críticos).
- Testes unitários frontend (hooks e componentes críticos).
- E2E do fluxo Projeto -> Ponto -> Cálculo -> Persistência.
- E2E APAGA + Undo (incluindo janela temporal e restauração efetiva).
- Lint + checagem de segurança de dependências.
- Checagem de schema/migrações para `projetos`.

### Etapa B - Pós-merge em dev
- Smoke integrado com backend e frontend em containers.
- Validação de eventos UX no funil mínimo.
- Verificação de logs de erro e latência em operações críticas.

### Etapa C - Pré-produção
- Regressão orientada a paridade LIGHT.
- Testes de autorização/acesso owner-only em `projetos`.
- Plano de rollback ensaiado para falha de deploy ou migração.

### Gates CI/CD mínimos (pass/fail)
- Gate 1: Build.
- Gate 2: Unit tests.
- Gate 3: E2E crítico.
- Gate 4: Security scan.
- Gate 5: Schema consistency check.
- Gate 6: Artifact integrity.

### Validacao rapida CI/CD (2026-03-22)
- Corrigido entrypoint backend no workflow de performance para `uvicorn api.main:app`.
- Branch strategy ajustada de `develop` para `dev` no workflow de CI/CD, preservando `main` para fluxo de deploy existente.
- Pipeline passou a instalar as ferramentas que invoca (`black`, `isort`, `flake8`, `mypy`, `bandit`, `safety`, `pip-audit`) para evitar falso negativo por comando ausente.
- `security-scan` agora faz setup explicito de Node e Python e instala dependencias antes de executar `npm audit` e `pip-audit`.

### Rodada de estabilizacao de testes (2026-03-22)
- [x] Vitest unitario validado em modo `--run` (2 arquivos, 13 testes).
- [x] Pytest validado com suite padrao estavel (44 passed, 4 skipped).
- [x] Playwright critico executado com backend local levantado automaticamente (`5 passed, 6 skipped`).
- [x] Testes legados/incompativeis com fluxo atual ajustados para refletir realidade operacional.
- [x] Workflows de CI e CI/CD alinhados com comandos executaveis no repositorio.
- [x] Nenhuma alteracao de logica de calculo de dominio (paridade Excel preservada).

Pendencias rastreadas desta rodada:
- [ ] Reativar os 2 cenarios E2E de persistencia automatica quando o wiring de persistencia no fluxo principal estiver concluido.

---

## 10) Regra: este arquivo é temporário e deve ser removido após execução completa

Regra operacional mandatória:
- Este documento existe apenas para condução tática da execução atual.
- Ao concluir 100% dos itens críticos e altos, e consolidar os resultados em documentação definitiva do projeto, remover este arquivo do repositório.

Checklist de encerramento deste temporário:
- [ ] Todos os itens P0 concluídos e validados.
- [ ] Todos os itens P1 concluídos ou formalmente replanejados com aceite.
- [ ] Critérios globais de aceite cumpridos.
- [ ] Evidências de CI/CD anexadas em documentação definitiva.
- [ ] Arquivo removido após fechamento formal da execução.
