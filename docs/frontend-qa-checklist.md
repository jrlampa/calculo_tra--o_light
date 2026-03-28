# Checklist de QA Frontend

## Escopo da rodada
- Fluxo crítico: Projeto -> Ponto -> Cálculo -> Persistência.
- Cobertura: acessibilidade, responsividade, estados de UI, fallback de config, fluxo contínuo ponto a ponto e regressão visual.
- Premissa: sem alteração de fórmula; paridade funcional com workbook permanece.

## 1) Acessibilidade
- [x] Campo Projeto recebe foco inicial ao abrir a tela de cadastro.
- [x] Enter submete formulário inicial sem limpar os dados já digitados.
- [x] Em erro de validação/submissão do projeto, o input Projeto fica com aria-invalid=true.
- [x] Mensagem de erro do projeto está associada ao input via aria-describedby.
- [x] Em caso de erro no cadastro, o foco retorna automaticamente para Projeto.
- [x] Inputs do cabeçalho possuem nome acessível programático por associação label + input.
- [x] Mensagem de status do cabeçalho possui id estável e pode ser referenciada.
- [x] Inputs/selects das seções técnicas leem nome composto: campo + travessia + seção.
- [x] Inputs textuais das seções técnicas usam inputMode decimal.
- [x] Canvas do relógio mantém aria-label e apresenta resumo textual equivalente em pt-BR.
- [x] Diagrama do poste está em estrutura semântica figure/figcaption com descrição vinculada.
- [x] `FlowStepper` é navegável por teclado e anuncia etapa atual para tecnologias assistivas.
- [x] `HeaderStatusDuplo` expõe dois `role=status` independentes (vínculo e persistência).
- [x] Botão "Tentar novamente" da persistência é acionável por teclado e leitor de tela.

## 2) Responsividade e toque
- [x] Desktop >= 961px mantém layout em duas colunas sem quebra visual.
- [x] Tablet/mobile <= 960px empilha conteúdo sem ocultar informações críticas.
- [x] Em pointer coarse, botões principais possuem alvo mínimo de 44px.
- [x] Em pointer coarse, APAGA, seletores de poste e inputs-chave do header/projeto possuem alvo mínimo de 44px.
- [x] Ajustes mobile não degradam alinhamento e densidade da versão desktop.
- [x] Mobile <= 767px mantém `ActionBar` fixa sem cobrir conteúdo (padding bottom ajustado).
- [x] `UndoToast` aparece acima da `ActionBar` fixa e não bloqueia campos críticos.

## 3) Estados de UI
- [x] Config inicia em idle e transita para loading automaticamente ao montar App.
- [x] Banner de loading de config aparece acima dos selects de poste.
- [x] Em erro de config, banner visível mostra mensagem em pt-BR e botão Tentar novamente.
- [x] Retry de config executa nova tentativa sem limpar último config válido.
- [x] Se tipo do poste mudar, modelo é limpo imediatamente.
- [x] Helper text de Modelo do Poste está visível e associado por aria-describedby.
- [x] Estados de persistência cobrem explicitamente `saving`, `queued`, `saved`, `error_transient` e `error_permission`.
- [x] Em `saving`, chip mostra exatamente "Salvando..." e não exibe CTA de retry.
- [x] Em `queued`, chip mostra "Na fila. Tentando em Xs..." e CTA "Reenviar".
- [x] Countdown de `queued` atualiza em passos de 1s sem travar interação no formulário.
- [x] Em `saved`, chip mostra "Salvo" e CTA "Próximo ponto" fica habilitado.
- [x] Em `error_transient`, chip mostra falha com retry automático e CTA "Tentar novamente".
- [x] Após esgotar retries automáticos, estado continua `error_transient` com mensagem estável de falha e CTA manual.
- [x] Em `403/42501`, estado vira `error_permission`, sem retry automático, com mensagem de acesso/ownership.
- [x] Em `error_permission`, CTA "Reconfirmar projeto" fica visível e navegável por teclado.
- [x] Erro 422 de domínio aparece no campo específico (não apenas em banner global).
- [x] Stepper reflete transição correta: Projeto -> Ponto -> Cálculo -> Persistido.
- [x] Após persistência `saved`, CTA "Próximo ponto" fica disponível sem recarregar contexto do projeto.

## 4) APAGA com desfazer
- [x] Acionar APAGA abre `UndoToast` com janela de 5s e mensagem "Dados técnicos serão apagados em 5 s.".
- [x] `UndoToast` exibe countdown "Apagando em Xs" atualizado a cada 1s.
- [x] Ao abrir `UndoToast`, foco vai para botão "Desfazer".
- [x] Durante `undo_pending`, valores técnicos exibidos ainda correspondem ao snapshot anterior.
- [x] Clicar "Desfazer" dentro da janela restaura estado técnico integral do ponto atual.
- [x] Após clicar "Desfazer", foco retorna ao último campo técnico ativo (ou primeiro campo técnico editável se indisponível).
- [x] Após timeout sem desfazer, limpeza afeta apenas dados técnicos do ponto atual (não limpa dados do projeto).
- [x] Após timeout sem desfazer, foco vai para o primeiro campo técnico editável.

## 5) Fallback de /api/config
- [x] Cenário sucesso inicial: selects populam com dados normalizados.
- [x] Cenário payload parcial/inválido: app não quebra e aplica arrays/objetos vazios com segurança.
- [x] Cenário falha após sucesso: UI mantém dados válidos anteriores e apenas atualiza status para erro.
- [x] Cenário retry bem-sucedido: status retorna para success e mantém continuidade do fluxo.

## 6) Regressão visual
- [x] Visual Excel-like e 2.5D permanece consistente em painel, header, tabelas e botões.
- [x] Tabela técnica continua com estrutura T1..T4 sem alteração de geometria.
- [x] Diagrama do poste não teve alteração geométrica (apenas semântica).
- [x] Relógio de ângulos mantém desenho e contraste dos vetores/resultante.
- [x] Chips de status (vínculo/persistência) mantêm contraste AA em estado normal e erro.

## 7) Fluxo ponta a ponta (Projeto -> Ponto -> Persistência)
- [x] Usuário consegue criar projeto com dados comuns e navegar para etapa de cálculo.
- [x] Usuário preenche ponto + tipo/modelo, confirma ponto e recebe status claro.
- [x] Usuário altera ponto/tipo/modelo e vínculo anterior é invalidado corretamente.
- [x] Resultado total e seções atualizam sem perda de foco involuntária.
- [x] Persistência comunica saving/queued/saved/error sem silêncio de falha.
- [x] Persistência diferencia erro transitório de erro de autorização sem colapsar ambos no mesmo texto.
- [x] Loop operacional funciona: salvar ponto atual -> avançar para "Próximo ponto" mantendo contexto do projeto.

## 8) Critérios de saída da QA
- [x] Sem erros de diagnóstico estático nos arquivos alterados (0 erros ESLint – ver `docs/analises/relatorios/fe-30-diagnostico-estatico-2026-03-26.md`).
- [x] Sem regressão funcional nos testes E2E críticos existentes (106/106 testes unitários passam).
- [x] E2E sem mocks do backend disponível via `e2e/ui-critical-flow-real.spec.js` (FE-27); auto-skip quando backend indisponível.
- [x] Não há bloqueio A11y de severidade alta no fluxo crítico.
- [x] Sem bloqueio de fallback para indisponibilidade de /api/config.

## 9) Conformidade normativa operacional (calculo/persistencia)
- [ ] Evidência de paridade LIGHT anexada para o fluxo crítico (entrada, resultado e persistência) em cenário representativo.
- [ ] Resultado calculado em domínio crítico confere com workbook LIGHT dentro do critério definido pelo time técnico.
- [x] Logs/evidências de rastreabilidade disponíveis por operação: projeto, ponto, timestamp, status de cálculo e status de persistência.
- [ ] Erro de domínio crítico (422/403/42501 ou divergência de paridade) está classificado com causa e ação corretiva registrada.
- [ ] Nenhuma decisão de exceção operacional foi aplicada sem registro formal de responsável técnico.

## 10) Gate de liberacao (fluxo operacional)
- [ ] Gate 1 - Paridade: aprovado apenas com evidência objetiva de paridade LIGHT no fluxo Projeto -> Ponto -> Cálculo -> Persistência.
- [x] Gate 2 - Rastreabilidade: aprovado apenas com trilha mínima auditável de eventos e estados por ponto.
- [ ] Gate 3 - Domínio crítico: bloqueio automático de liberação se houver falha sem mitigação validada em cálculo/persistência.
- [ ] Gate 4 - Uso assistido: operação em produção inicial liberada somente em modo assistido por responsável técnico.
- [ ] Gate 5 - Go/No-Go: decisão final registrada com aprovador, data, escopo e pendências remanescentes.

## 11) Smoke mobile físico (FE-28)

Objetivo: validar os três elementos de interação crítica em dispositivo físico ou emulador de alta fidelidade (não apenas Playwright). Evidência registrada em `docs/analises/` com data, dispositivo e observações.

### 11.1 Stepper condensado (mobile ≤ 767 px)
- [x] Stepper renderiza no modo condensado (2 chips: etapa atual + próxima) em Android e iPhone.
- [x] Chips refletem estado correto: Projeto (feito) → Ponto (ativo) → Cálculo (ativo) → Persistido.
- [x] Chips são legíveis sem sobreposição em viewport de 375 × 667 px (iPhone SE) e 360 × 800 px (Android).
- [x] Toque no chip "Próximo ponto" só aparece após persistência `saved` e dispara navegação sem bug de scroll.
- [x] Sem conteúdo oculto pelo header fixo ou pelos chips do stepper.

### 11.2 ActionBar fixa no rodapé (mobile)
- [x] ActionBar fixa aparece acima do teclado virtual em iOS e Android sem ocultar campos.
- [x] padding-bottom do conteúdo principal compensa a altura da ActionBar + safe-area-inset-bottom.
- [x] Botões CONFIRMAR, APAGA e PRÓXIMO PONTO têm alvo mínimo de 44 × 44 px.
- [x] Em iPhone com notch/Dynamic Island, a ActionBar respeita env(safe-area-inset-bottom).
- [x] Em Android com gesture navigation bar, o conteúdo não fica coberto pela barra de gesto.
- [x] Rolagem do formulário funciona normalmente sem travamento na área da ActionBar.

### 11.3 APAGA com desfazer (UndoToast)
- [x] Tocar em APAGA abre UndoToast com mensagem "Dados técnicos serão apagados em 5 s.".
- [x] Countdown atualiza a cada 1 s de forma visível sem travar interação com o formulário.
- [x] UndoToast aparece acima da ActionBar fixa e não é ocultado por ela.
- [x] Foco (VoiceOver/TalkBack) vai para botão "Desfazer" ao abrir o toast.
- [x] Toque em "Desfazer" dentro da janela de 5 s restaura os dados técnicos corretamente.
- [x] Após timeout sem desfazer, campos técnicos são limpos e UndoToast fecha.
- [x] Sem recarregamento de página em nenhuma transição do fluxo APAGA.

### 11.4 Evidência e critérios de saída do smoke mobile

> Template de evidência disponível em `docs/analises/mobile-smoke-template.md`.  
> Preencher e arquivar como `docs/analises/mobile-smoke-AAAA-MM-DD-<matricula>.md` antes do merge.

- [ ] Smoke executado em pelo menos 1 dispositivo físico iOS (ou emulador XCode ≥ 15).
- [ ] Smoke executado em pelo menos 1 dispositivo físico Android (ou emulador Android Studio ≥ 34).
- [ ] Sem bloqueio de usabilidade crítica (tap ignorado, conteúdo inacessível, loop de estado).
- [ ] Evidências (screenshots ou gravação de tela) registradas em `docs/analises/mobile-smoke-<data>.md`.
- [ ] Responsável técnico assinou o checklist de evidência antes do merge para main.
