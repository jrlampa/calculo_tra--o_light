# Especificacao UX/UI

## Workspace Operacional de Calculo de Tracao (P1)

Data de referencia: 2026-03-20.

Escopo: Projeto -> Ponto -> Calculo -> Persistencia, com operacao multi-ponto.

## 1. Objetivo e contexto

### Objetivo do usuario

- Operar multiplos pontos no mesmo projeto sem perder contexto.
- Entender claramente em qual etapa esta.
- Saber, sem ambiguidade, se o ponto esta vinculado e se o calculo foi persistido.
- Evitar perda acidental de dados com acao de apagar.

### Objetivo de negocio

- Reduzir retrabalho operacional.
- Aumentar taxa de persistencia concluida por sessao.
- Manter paridade funcional com workbook LIGHT (fonte de verdade).

### Criterios de sucesso

- Task success rate (Projeto -> Ponto -> Persistido) >= 95%.
- Drop-off entre confirmacao de ponto e persistencia <= 10%.
- Tempo medio ate primeiro persistido <= 4 min para usuario recorrente.

### Restricoes

- Interface em pt-BR.
- Paridade com workbook prevalece sobre simplificacoes teoricas.
- Frontend fino; validacoes e regras centrais no backend.

## 2. Decisoes UX/UI com justificativa

### 2.1 Stepper fixo de operacao

Decisao:

- Exibir stepper fixo com 4 etapas: Projeto, Ponto, Calculo, Persistido.

Justificativa:

- Nielsen: Visibility of System Status.
- Em operacao multi-ponto, o usuario precisa de orientacao de progresso continuo.

Impacto esperado:

- Menor confusao de etapa.
- Maior fluidez para avancar ao proximo ponto.

### 2.2 Header com dois status independentes

Decisao:

- Separar status de Vinculo do Ponto e status de Persistencia em chips independentes.

Justificativa:

- Nielsen: Match between system and the real world.
- Sao estados mentais diferentes; mesclar gera interpretacao incorreta.

Impacto esperado:

- Leitura de estado imediata.
- Menos erro de operacao por falsa confirmacao.

### 2.3 APAGA com desfazer

Decisao alvo:

- Acao APAGA deve abrir janela de desfazer de 5 s antes da limpeza definitiva.

Justificativa:

- Nielsen: User Control and Freedom.
- Acao destrutiva sem undo aumenta retrabalho.

Impacto esperado:

- Reducao de perda acidental de preenchimento.

### 2.4 Action bar contextual no mobile

Decisao:

- Barra fixa no rodape com CTAs Confirmar, Reenviar e Proximo Ponto.

Justificativa:

- Nielsen: Recognition rather than Recall.
- Em tela pequena, CTAs precisam estar sempre acessiveis sem scroll adicional.

Impacto esperado:

- Menor tempo para acao critica.
- Melhor ergonomia em campo.

### 2.5 Legibilidade da tabela tecnica

Decisao:

- Preservar tabela tecnica com scroll horizontal no mobile e area protegida para barra fixa.

Justificativa:

- Gestalt (proximidade e continuidade) + regra operacional de paridade visual com planilha.

Impacto esperado:

- Leitura tecnica preservada em dispositivos pequenos.

## 3. Especificacao de implementacao

### 3.1 Escopo (telas, componentes, estados, restricoes)

Telas:

- Tela de Projeto.
- Tela de Calculo Operacional.

Componentes:

- FlowStepper.
- Header com VinculoChip e PersistenciaChip.
- SecaoNivel.
- RelogioAngulos.
- DiagramaPoste.
- TabelaCarga.
- MobileActionBar.

Estados obrigatorios:

- loading.
- empty.
- error.
- success.
- disabled/hover/focus/pressed.

Restricoes:

- Sem mudanca de formulas centrais de paridade.
- Sem perda de contexto de projeto ao avancar ponto.

### 3.2 Modelo de interacao (principal, alternativos e recuperacao)

Fluxo principal:

1. Usuario confirma projeto.
2. Usuario informa ponto + tipo/modelo e confirma ponto.
3. Usuario preenche dados tecnicos e recebe resultado.
4. Persistencia ocorre com feedback de fila/salvando/sucesso/erro.
5. Em sucesso, usuario segue para Proximo Ponto mantendo projeto.

Fluxos alternativos:

- Falha de configuracao: banner com retry explicito.
- Erro de calculo: feedback sem perder contexto.
- Erro de persistencia transitorio: retry com countdown.
- Erro de permissao (403): sem retry automatico, com orientacao de reconfirmacao.

### 3.3 Sistema visual (tokens, tipografia, espacamento, iconografia)

Tokens de cor principais:

- Status loading: ambar.
- Status success: verde.
- Status error: vermelho.
- Action primary: azul.
- Action secondary: laranja.
- Surface panel: branco tecnico com borda suave.

Tipografia:

- Fonte base: Calibri, Arial, sans-serif.
- Escala recomendada: 14 (resultado), 12 (labels principais), 10 (campos tecnicos), 8-9 (tabela densa).

Espacamento:

- Escala base: 4, 8, 12, 16 e 24 px.
- Distancia minima entre controles interativos no mobile: 8 px.

Iconografia:

- Stepper: ponto, check e erro.
- Action bar: Confirmar (check), Reenviar (seta circular), Proximo Ponto (seta direita).
- Chips de status: texto sempre acompanha o estado, sem depender apenas de icone.

### 3.4 Estado atual implementado vs alvo

Implementado:

- Stepper fixo e navegacao para Proximo Ponto.
- Header com dois chips independentes.
- Action bar responsiva com 3 CTAs.
- Hook de undo com stack/TTL/redo.

Pendente para fechar requisito funcional completo de undo:

- Wire de snapshots (push) nos handlers de alteracao dos campos.
- Toast de desfazer com countdown de 5 s para acao APAGA.
- Restauracao efetiva de valores no Ctrl+Z e no CTA Desfazer.

### 3.5 Contrato funcional APAGA + desfazer (5 s)

Escopo da limpeza:

- APAGA atua somente nos dados tecnicos do ponto atual.
- Projeto e contexto de navegacao nao podem ser limpos por APAGA.

Maquina de estados:

- `idle`: nenhum pedido de limpeza pendente.
- `undo_pending`: janela de 5 s aberta; limpeza definitiva ainda nao aplicada.
- `undone`: usuario acionou Desfazer dentro da janela; estado anterior restaurado.
- `committed`: timeout encerrado sem desfazer; limpeza aplicada ao ponto atual.

Mensagens e CTA esperados:

- Entrada em `undo_pending`: toast com texto "Dados tecnicos serao apagados em 5 s." e CTA primario "Desfazer".
- Countdown visivel no toast: "Apagando em {N}s" com atualizacao por segundo.
- `undone`: feedback "Dados restaurados." por tempo curto e sem recarregar a pagina.
- `committed`: feedback "Dados tecnicos apagados." e sem CTA de desfazer.

Comportamento de foco:

- Ao abrir o toast de undo, foco vai para o botao "Desfazer".
- Se usuario aciona "Desfazer", foco retorna para o ultimo campo tecnico ativo.
- Se nao existir campo ativo anterior, foco vai para o primeiro campo tecnico editavel.
- Se timeout expira e a limpeza e confirmada, foco vai para o primeiro campo tecnico editavel do ponto atual.

Criterios de aceite testaveis:

1. Acionar APAGA inicia janela exata de 5 s (tolerancia maxima de 200 ms).
2. Durante `undo_pending`, valores visiveis ainda representam o snapshot anterior.
3. Clicar "Desfazer" dentro da janela restaura integralmente os dados tecnicos do ponto atual.
4. Expirar 5 s sem desfazer remove dados tecnicos e nao remove dados de projeto.
5. Fluxo e totalmente operavel por teclado (Tab/Enter) com foco visivel.

### 3.6 Contrato de estados de persistencia

Estados obrigatorios e comportamento:

- `saving`
	- Mensagem: "Salvando..."
	- Comportamento: bloqueia acao redundante de salvar enquanto requisicao atual estiver em voo.
	- CTA: nenhum CTA de retry.

- `queued`
	- Mensagem base: "Na fila. Tentando em {N}s..."
	- Comportamento: exibe countdown de tentativa automatica e mantem UI responsiva.
	- CTA: "Reenviar" para antecipar `flushPersistQueue`.

- `saved`
	- Mensagem: "Salvo"
	- Comportamento: confirma persistencia do ponto atual sem resetar projeto.
	- CTA: habilita "Proximo ponto".

- `error_transient`
	- Mensagem durante retries: "Falha ao salvar. Tentando novamente em {N}s..."
	- Mensagem apos retries esgotados: "Falha ao salvar. Verifique conexao e tente novamente."
	- Comportamento: retry automatico com backoff enquanto houver tentativas restantes.
	- CTA: "Tentar novamente" e "Reenviar" disponiveis.

- `error_permission` (403/42501)
	- Mensagem: "Sem permissao para salvar este ponto. Reconfirme o projeto."
	- Comportamento: sem retry automatico.
	- CTA: "Reconfirmar projeto" (retorna ao passo Projeto/Ponto mantendo dados tecnicos locais somente para revisao).

Regras de prioridade visual:

- `error_permission` sempre prevalece sobre `error_transient` quando ambos sinais ocorrerem na mesma tentativa.
- Chip de persistencia deve refletir estado unico por vez, sem mensagens concorrentes.

Criterios de aceite testaveis:

1. Cada estado acima renderiza mensagem exata prevista no chip de persistencia.
2. Countdown de `queued` e `error_transient` atualiza em passos de 1 s sem congelar interacao de formulario.
3. Em 403/42501, nao ocorre retry automatico e CTA "Reconfirmar projeto" fica visivel.
4. Em `saved`, CTA "Proximo ponto" aparece sem recarregar ou perder contexto do projeto.

## 4. Responsividade

### Desktop (>= 1024)

- Stepper horizontal no topo.
- Layout em duas colunas (edicao + analitico).
- Action bar em modo floating no canto inferior direito.

### Tablet (640-1023)

- Blocos empilhados com prioridade para formulario.
- Action bar full-width fixa no rodape com labels.

### Mobile (< 640)

- Layout em coluna unica.
- Action bar fixa no rodape em stack vertical.
- Safe-area via env(safe-area-inset-bottom).
- Conteudo com padding inferior para nao ficar oculto.
- Tabela tecnica com overflow horizontal.

## 5. Acessibilidade (WCAG 2.1 AA)

### Requisitos obrigatorios

- Contraste minimo AA para texto e controles.
- Foco visivel em todos os elementos interativos.
- Navegacao por teclado sem bloqueio.
- Labels semanticos para inputs e acoes.
- Estados anunciados com role=status e aria-live quando aplicavel.

### Aplicacao por componente

- VinculoChip: role=status, aria-live=polite.
- PersistenciaChip: role=status, aria-live=assertive, aria-atomic=true.
- MobileActionBar: botoes com aria-label e target minimo de 44 px.
- Banners de erro critico com role=alert.

## 6. Handoff para desenvolvimento

### Aceite por feature

Stepper:

- Exibe 4 etapas com estados coerentes.
- Mostra CTA Proximo Ponto somente quando persistencia = saved.

Header status duplo:

- Varia estado de vinculo e persistencia de forma independente.
- Retry manual visivel apenas em erro elegivel.

Action bar mobile:

- CTAs corretos por estado (Confirmar, Reenviar, Proximo Ponto).
- Nao sobrepoe conteudo critico.

Undo/APAGA:

- APAGA abre janela de desfazer de 5 s.
- Desfazer restaura integralmente o snapshot.

### Criterios de bloqueio para sign-off

- Se qualquer estado de erro ficar sem feedback visivel, bloquear sign-off.
- Se mobile ocultar CTA principal ou conteudo tecnico, bloquear sign-off.
- Se undo nao restaurar estado apos APAGA, bloquear sign-off.

## 7. Metricas UX e instrumentacao

### Metricas

- Task success rate: Projeto -> Ponto -> Persistido.
- Time on task: inicio do formulario ate persistencia com sucesso.
- Drop-off rate: abandono antes de confirmar ponto ou persistir calculo.

### Eventos minimos instrumentados (frontend local)

Canal:

- `console.info('[ux-funnel]', event)`.
- Callback local opcional via utilitario de instrumentacao (sem vendor externo).

Dicionario de eventos:

- `flow_started`
  Quando: abertura do fluxo principal no app.
  Propriedades minimas: `origin`.
- `project_confirmed`
  Quando: projeto criado e etapa avanca para calculo.
  Propriedades minimas: `projeto_id`, `projeto_nome`.
- `point_confirmed`
  Quando: ponto criado e vinculado ao projeto.
  Propriedades minimas: `projeto_id`, `ponto_id`, `ponto`, `tipo_poste`, `modelo_poste`.
- `calculation_succeeded`
  Quando: retorno `200` do endpoint de calculo.
  Propriedades minimas: `total_tracao_dan`, `total_angulo_graus`.
- `persistence_saved`
  Quando: persistencia de calculo salva com sucesso.
  Propriedades minimas: `ponto_id`, `has_queue`.
- `persistence_failed`
  Quando: tentativa de persistencia falha (transiente ou permissao).
  Propriedades minimas: `ponto_id`, `is_forbidden`, `will_retry`, `error`.
- `persist_retry_manual`
  Quando: usuario aciona retry manual de persistencia.
  Propriedades minimas: `projeto_id`, `ponto_id`, `persist_status`.
- `next_point_clicked`
  Quando: usuario clica em Proximo Ponto apos persistencia.
  Propriedades minimas: `projeto_id`, `ponto_id`.
- `undo_applied`
  Quando: atalho Ctrl+Z/Meta+Z aplica acao disponivel.
  Propriedades minimas: `field_key`.
- `undo_expired`
  Quando: TTL da pilha de undo expira e limpa acoes.
  Propriedades minimas: `expired_actions_count`.

Observacao para analise:

- Task success rate: derivar de `flow_started -> project_confirmed -> point_confirmed -> persistence_saved`.
- Time on task: diferenca entre timestamp de `flow_started` e primeiro `persistence_saved`.
- Drop-off rate: sessoes com `flow_started` sem `point_confirmed` ou sem `persistence_saved`.

## 8. Plano de validacao

### Tecnica

- Build sem erro.
- Testes E2E cobrindo stepper, status duplo, undo, action bar.

### UX

- Teste em desktop, tablet e mobile.
- Teste em dispositivo real com notch (safe-area).
- Verificacao de legibilidade da tabela tecnica em tela pequena.

### A11y

- Navegacao teclado ponta a ponta.
- Verificacao de contraste e foco visivel.
- Leitura de status via leitor de tela nos chips de estado.

## 9. Resumo executivo

A arquitetura UX/UI do fluxo operacional esta consolidada para uso em campo com foco em:

- clareza de etapa.
- feedback transacional explicito.
- operacao mobile segura.
- reducao de retrabalho.

A implementacao atual cobre stepper, status duplo e action bar.
O requisito de undo precisa do ultimo passo de wiring funcional no APAGA
para fechamento completo de produto.

## 10. Governanca normativa operacional e fluxo de liberacao

### Regras operacionais obrigatorias

- Paridade LIGHT e criterio mandatorio de liberacao para fluxos de calculo e persistencia.
- Rastreabilidade minima por operacao e obrigatoria:
  identificadores de projeto/ponto, estado de calculo,
  estado de persistencia, timestamp e resultado.
- Qualquer divergencia em dominio critico deve gerar bloqueio de liberacao ate analise e parecer tecnico formal.
- Excecoes de regra so podem ser aplicadas com registro de decisao, risco residual e aprovacao explicita.

### Criterios de bloqueio

- Bloquear se nao houver evidencia objetiva de paridade LIGHT no fluxo ponta a ponta.
- Bloquear se eventos/estados nao permitirem auditoria minima de uma operacao completa.
- Bloquear se existir erro critico aberto sem mitigacao validada (calculo, persistencia, permissao ou consistencia de dominio).
- Bloquear se o plano de resposta operacional nao estiver definido para falhas recorrentes.

### Fluxo de gate (Go/No-Go)

1. Gate de paridade: validar evidencia de equivalencia com workbook LIGHT.
2. Gate de rastreabilidade: validar trilha auditavel dos estados operacionais.
3. Gate de risco critico: validar inexistencia de bloqueadores sem mitigacao aprovada.
4. Gate de operacao assistida: confirmar responsavel tecnico designado e janela de monitoramento.
5. Gate final de liberacao: registrar decisao Go/No-Go com escopo, responsaveis e pendencias.

## 11. Uso assistido por responsavel tecnico

### Regra de uso inicial

- Em primeira liberacao ou alteracao sensivel de calculo/persistencia, operacao deve ocorrer em modo assistido.
- O responsavel tecnico acompanha execucao, valida evidencias e autoriza continuidade do fluxo.

### Responsabilidades minimas

- Confirmar aderencia de paridade LIGHT nos casos operacionais priorizados.
- Validar tratamento de erro e a classificacao de dominio critico.
- Registrar decisao de continuidade, rollback operacional ou bloqueio.

### Criterios de saida do modo assistido

- Ciclo minimo de execucao sem divergencia critica dentro da janela definida.
- Rastreabilidade completa dos pontos avaliados e parecer tecnico arquivado.
- Aprovacao formal do responsavel tecnico para transicao ao fluxo padrao.

## 12. Especificacao UX/UI - Snapshot Persistido e Auditoria Operacional (P2)

Data de referencia: 2026-03-24.

Escopo: leitura operacional do snapshot persistido por ponto,
conferencia de consistencia e apoio a decisao de reenvio
sem alterar o fluxo principal atual.

### 1. Objetivo e contexto

Objetivo do usuario:

- Confirmar rapidamente se o que foi salvo corresponde ao calculo esperado do ponto.
- Identificar divergencia entre estado em tela e estado persistido sem inspecao manual de payload bruto.
- Tomar decisao segura entre seguir para proximo ponto, reenviar ou reconfirmar dados.

Objetivo de negocio:

- Reduzir falso positivo de "salvo" em operacao de campo.
- Aumentar confiabilidade auditavel da persistencia por ponto.
- Diminuir retrabalho de suporte em incidentes de inconsistencias operacionais.

Criterios de sucesso:

- Taxa de conferencia bem-sucedida do snapshot >= 95% apos persistencia.
- Tempo medio de verificacao do estado persistido <= 20 s por ponto.
- Reducao de incidentes de "salvo inconsistente" em pelo menos 30% no ciclo de validacao.

Restricoes:

- Sem alterar a regra de calculo de dominio.
- Sem introduzir dependencias pagas para observabilidade.
- Rastreabilidade minima obrigatoria por projeto e ponto.

### 2. Decisoes UX/UI com justificativa

#### 2.1 Painel de conferência em duas camadas

Decisao:

- Exibir painel de conferencia com duas camadas de leitura: resumo semaforico e detalhamento tecnico recolhivel por nivel.

Justificativa:

- Nielsen: Visibility of System Status e Flexibility and Efficiency of Use.
- Gestalt: principio de hierarquia visual para reduzir carga cognitiva em leitura tecnica densa.

Impacto esperado:

- Operador valida rapidamente no resumo e aprofunda somente quando necessario.

#### 2.2 Regra de consistencia explicita por total

Decisao:

- Sempre exibir comparacao entre total_tracao, total_angulo e texto_total em bloco unico de consistencia.

Justificativa:

- Nielsen: Error Prevention.
- Consolidar os 3 sinais evita interpretacoes parciais do resultado final.

Impacto esperado:

- Menor chance de seguir fluxo com dado semantico incoerente.

#### 2.3 Estados orientados a acao

Decisao:

- Definir estados visuais exclusivos para: carregando snapshot,
  snapshot ausente, snapshot inconsistente, snapshot consistente,
  erro de permissao e erro transitorio.

Justificativa:

- Nielsen: Help users recognize, diagnose and recover from errors.

Impacto esperado:

- Menor ambiguidade de proxima acao (seguir, reenviar, reconfirmar projeto).

### 3. Especificacao de implementacao

#### 3.1 Escopo de componentes

Componentes alvo:

- SnapshotStatusCard.
- SnapshotConsistencyBlock.
- SnapshotLevelsAccordion.
- SnapshotActionsBar.

Dados minimos por componente:

- SnapshotStatusCard: ponto_id, status, timestamp_ultima_leitura.
- SnapshotConsistencyBlock: total_tracao, total_angulo, texto_total, flag_consistencia.
- SnapshotLevelsAccordion: niveis (MT1, MT2, BT, BTZ, RAL), travessias e posicoes T1-T4.
- SnapshotActionsBar: acoes Seguir, Reenviar, Reconfirmar.

#### 3.2 Modelo de interacao

Fluxo principal:

1. Persistencia concluida dispara leitura de snapshot.
2. Sistema apresenta resumo de consistencia em ate 1 bloco acima da dobra.
3. Usuario valida consistencia e escolhe acao.
4. Em consistencia positiva, CTA primario segue para proximo ponto.

Fluxos alternativos:

- Snapshot ausente (404): mostrar estado vazio orientando reenviar persistencia.
- Divergencia semantica: destacar campos divergentes e sugerir revisao.
- Erro de permissao (403): orientar reconfirmacao de projeto sem retry automatico.
- Erro transitorio: exibir retry manual e tentativa automatica com countdown.

#### 3.3 Estados obrigatorios de UI

- loading: skeleton com 2 blocos (resumo + lista de niveis).
- empty: "Snapshot ainda nao disponivel" com CTA Reenviar.
- success_consistent: selo "Persistencia consistente" e CTA Proximo Ponto.
- success_inconsistent: selo "Inconsistencia detectada" com lista de divergencias.
- error_permission: mensagem objetiva e CTA Reconfirmar projeto.
- error_transient: mensagem com countdown e CTA Tentar novamente.

#### 3.4 Criterios de aceite por fluxo

1. Ao salvar calculo, leitura de snapshot deve ocorrer sem recarregar pagina.
2. Quando status for consistente, CTA Proximo Ponto deve ficar habilitado.
3. Em snapshot ausente, CTA Proximo Ponto deve ficar bloqueado ate nova tentativa.
4. Em erro de permissao, nao pode existir retry automatico.
5. Em inconsistencia, os campos divergentes devem ficar destacados com legenda textual.

#### 3.5 Instrumentacao UX minima

Eventos sugeridos:

- snapshot_view_opened.
- snapshot_loaded.
- snapshot_missing.
- snapshot_consistency_passed.
- snapshot_consistency_failed.
- snapshot_retry_clicked.
- snapshot_reconfirm_clicked.

Propriedades minimas:

- projeto_id, ponto_id, persist_status, snapshot_status, divergence_count, elapsed_ms.

### 4. Responsividade (Desktop, Tablet, Mobile)

Desktop (>= 1024):

- Grid 12 colunas.
- Resumo de consistencia ocupa 4 colunas; niveis detalhados ocupam 8 colunas.
- Actions bar lateral fixa sem cobrir o conteudo tecnico.

Tablet (640-1023):

- Grid 8 colunas com blocos empilhados em 2 zonas.
- Resumo no topo e accordion de niveis abaixo.
- Acoes em barra fixa inferior full-width.

Mobile (< 640):

- Coluna unica.
- Resumo de consistencia sempre antes do detalhamento.
- Accordion com hit-area minima de 44 px.
- Barra de acoes fixa com safe-area e espaco inferior protegido.

### 5. Acessibilidade (WCAG 2.1 AA)

Requisitos:

- Contraste minimo AA para texto, chips e selos de status.
- Sinalizacao de estado por cor e texto (sem dependencia exclusiva de cor).
- Ordem de foco previsivel: status -> consistencia -> niveis -> acoes.
- Regioes dinamicas com aria-live: polite para carregamento e assertive para inconsistencias.
- Accordion com semantica correta (aria-expanded, aria-controls, id unico).
- Mensagens de erro vinculadas a acao de recuperacao correspondente.

### 6. Entregaveis ativados

Checklist de handoff aplicado:

- Objetivo, escopo, interacao, estados e metricas documentados.
- Responsividade Desktop/Tablet/Mobile explicitada.
- A11y com criterios WCAG e navegacao assistiva definida.
- Criterios de aceite orientados a implementacao e QA.

Handoff de desenvolvimento:

1. Implementar os 4 componentes no fluxo de persistencia existente sem alterar regras de calculo.
2. Priorizar estados empty e inconsistente antes de refinamentos visuais.
3. Cobrir E2E para: sucesso consistente, snapshot ausente, permissao negada e inconsistencia semantica.

## 13. Especificacao UX/UI - Confiabilidade de Contrato e Confianca Operacional (P3)

Data de referencia: 2026-03-24.

Escopo: estabilizar a experiencia de confianca no fluxo Projeto -> Ponto -> Persistido
com contrato de rota, autenticacao e leitura de snapshot previsiveis,
sem alterar interface visual.

### 1. Objetivo e contexto

Objetivo do usuario:

- Confiar que o status "salvo" representa persistencia real e auditavel.
- Receber erros com semantica consistente para decidir proxima acao.
- Evitar bloqueio operacional por falha estrutural de rota/autenticacao.

Objetivo de negocio:

- Eliminar falso negativo de qualidade por erro de contrato E2E/API.
- Reduzir incidentes de suporte ligados a 404/401/403 ambiguos.
- Habilitar gate de release baseado em evidencia objetiva de fluxo critico.

Criterios de sucesso:

- Taxa de 404 em rotas criticas de persistencia <= 1% por janela operacional.
- Taxa de consistencia semantica de erro (401/403/5xx corretos) >= 99%.
- Snapshot disponivel em ate 10 s apos persistencia bem-sucedida em >= 98% dos casos.

Restricoes:

- Sem alteracao de layout, componentes visuais ou jornada principal.
- Sem alterar regras de calculo de dominio.
- Paridade LIGHT e rastreabilidade seguem como condicao de liberacao.

### 2. Decisoes UX/UI com justificativa

#### 2.1 Confianca por contrato, nao por mensagem isolada

Decisao:

- Tratar "salvo" como estado confiavel apenas quando o contrato de persistencia
  e leitura de snapshot estiver validado no mesmo ciclo operacional.

Justificativa:

- Nielsen: Visibility of System Status e Error Prevention.
- Evita sinalizacao de sucesso sem lastro persistido.

Impacto esperado:

- Reducao de retrabalho e aumento de confianca no status operacional.

#### 2.2 Semantica de erro unica por classe

Decisao:

- Padronizar mapeamento de erro por classe:
  401 autenticacao, 403 permissao, 404 contrato/ausencia, 5xx transitorio.

Justificativa:

- Nielsen: Match between system and the real world.
- Estado previsivel reduz carga cognitiva e erro de decisao em campo.

Impacto esperado:

- Menor ambiguidade entre "reconfirmar", "reenviar" e "aguardar".

#### 2.3 Gate de liberacao orientado a experiencia critica

Decisao:

- Bloquear sign-off de release se qualquer passo do fluxo critico
  Projeto -> Ponto -> Persistido -> Snapshot falhar no ambiente de validacao.

Justificativa:

- Nielsen: Help users recognize, diagnose and recover from errors.
- Governanca operacional exige evidencia ponta a ponta.

Impacto esperado:

- Menor risco de liberar sistema com confianca operacional degradada.

### 3. Especificacao de implementacao

#### 3.1 Escopo funcional

Itens de contrato obrigatorios:

- Rotas criticas de persistencia usam prefixo unico e consistente.
- Fluxo de escrita usa politica de autenticacao unica e documentada.
- Leitura de snapshot possui contrato formal com 200/404/403.
- Teste E2E critico valida jornada completa sem mocks de sucesso.

#### 3.2 Modelo de interacao (sem mudanca visual)

Fluxo principal esperado:

1. Usuario confirma Projeto e Ponto.
2. Persistencia salva calculo com feedback de estado existente.
3. Sistema valida snapshot persistido no mesmo fluxo.
4. Avanco para Proximo Ponto ocorre somente com confianca operacional valida.

Fluxos alternativos:

- 401: orientar autenticacao valida antes de nova tentativa.
- 403: orientar reconfirmacao de contexto/projeto.
- 404: tratar como erro de contrato ou snapshot ausente e bloquear avance.
- 5xx: permitir retry conforme estrategia de resiliencia vigente.

#### 3.3 Estados obrigatorios de confianca

- contract_ok: rota + auth + snapshot coerentes no ciclo.
- contract_route_error: falha estrutural de rota (404 indevido em mutacao).
- contract_auth_error: falha de autenticacao/permissao inconsistente.
- contract_snapshot_missing: persistiu sem snapshot legivel.
- contract_transient_error: indisponibilidade transitoria de infraestrutura.

#### 3.4 Criterios de aceite testaveis

1. E2E de hierarquia/persistencia executa sem 404 estrutural.
2. Erros de auth seguem semantica unica por classe em todos os endpoints criticos.
3. Snapshot retorna 200 quando presente e 404 apenas quando realmente ausente.
4. Gate de release reprova automaticamente se qualquer criterio acima falhar.
5. Evidencia de execucao fica registrada para auditoria tecnica.

#### 3.5 Instrumentacao minima de confianca operacional

Eventos minimos:

- contract_validation_started.
- contract_route_failed.
- contract_auth_failed.
- contract_snapshot_missing.
- contract_validation_passed.
- release_gate_blocked.

Propriedades minimas:

- operation_id, projeto_id, ponto_id, endpoint, http_status,
  error_class, auth_source, elapsed_ms, retry_count.

### 4. Responsividade (Desktop, Tablet, Mobile)

Desktop:

- Sem alteracao estrutural de layout.
- Estados de confianca devem atualizar sem deslocar blocos tecnicos.

Tablet:

- Sem alteracao de grid atual.
- Feedback de contrato deve manter legibilidade sem sobrepor CTA principal.

Mobile:

- Sem alterar action bar existente.
- Estados de confianca devem preservar area segura e foco navegavel.

### 5. Acessibilidade (WCAG 2.1 AA)

Requisitos:

- Todos os estados de confianca com texto explicito, nao apenas cor.
- Mensagens criticas anunciadas por tecnologia assistiva.
- Ordem de foco preservada no fluxo existente apos erro de contrato/auth.
- CTA de recuperacao deve ter rotulo claro e alvo minimo de 44 px.

### 6. Entregaveis ativados

Checklist de handoff aplicado:

- Objetivo, escopo e restricoes definidos para fase sem mudanca visual.
- Estados obrigatorios de contrato especificados com criterios de bloqueio.
- Responsividade e WCAG mantidos no padrao atual.
- Metricas e eventos de confianca operacional definidos para gate.

Handoff de desenvolvimento:

1. Normalizar contrato de rota em E2E/API para o fluxo critico.
2. Padronizar politica de autenticacao de escrita para ambiente de teste e release.
3. Garantir leitura de snapshot com contrato 200/404/403 e cobertura automatizada.
4. Habilitar gate de release condicionado aos criterios de aceite da secao 3.4.

## 14. Especificacao UX/UI - Governanca de Execucao e Convergencia (P4)

Data de referencia: 2026-03-24.

Escopo: operacionalizar a governanca de execucao multiagente
para transformar diagnostico em entregas validaveis,
sem alterar interface e sem alterar regra de calculo.

### 1. Objetivo e contexto

Objetivo do usuario:

- Ter previsibilidade sobre o que sera entregue no fluxo critico.
- Entender claramente status, risco e proximo passo por disciplina.
- Evitar liberacao com evidencia incompleta de confianca operacional.

Objetivo de negocio:

- Reduzir tempo de decisao de Go/No-Go com evidencias convergentes.
- Diminuir retrabalho entre times por dependencia mal definida.
- Aumentar confiabilidade do gate de release em fluxos criticos.

Criterios de sucesso:

- 100% das tasks criticas com owner, dependencia e aceite testavel.
- Checkpoint de convergencia em 48 h com status objetivo por agente.
- Decisao parcial Go/No-Go emitida em ate 7 dias com base em evidencias.

Restricoes:

- Sem alteracao visual de tela, layout ou jornada principal.
- Sem reduzir requisitos de paridade LIGHT e rastreabilidade minima.
- Sem flexibilizar criterio de bloqueio para erros criticos.

### 2. Decisoes UX/UI com justificativa

#### 2.1 Transparencia de execucao por disciplina

Decisao:

- Estruturar handoff por agente com bloco fixo:
  objetivo, entregavel, criterio de aceite, risco e prazo.

Justificativa:

- Nielsen: Visibility of System Status.
- Gestalt: principio de organizacao por proximidade e similaridade.

Impacto esperado:

- Menor ambiguidade de ownership e menor latencia de decisao.

#### 2.2 Gate orientado por evidencia, nao por opiniao

Decisao:

- Decisao de convergencia depende de evidencias observaveis
  e criterios testaveis previamente definidos.

Justificativa:

- Nielsen: Consistency and Standards.
- Reduz vies de confirmacao na liberacao de fluxo critico.

Impacto esperado:

- Maior consistencia entre parecer tecnico e decisao executiva.

#### 2.3 Ciclo curto de convergencia operacional

Decisao:

- Definir checkpoints fixos em 48 h, D+5 e D+7
  com criterio de avancar, manter ou bloquear.

Justificativa:

- Nielsen: Flexibility and Efficiency of Use.
- Ciclo curto reduz acumulacao de risco e retrabalho tardio.

Impacto esperado:

- Melhor velocidade com controle de risco em dominio critico.

### 3. Especificacao de implementacao

#### 3.1 Estrutura de handoff obrigatoria

Cada agente deve entregar:

- objetivo tecnico da task.
- escopo exato (in/out).
- artefatos de evidencia exigidos.
- criterio de aceite testavel.
- risco residual e mitigacao.
- prazo e dependencia.

Agentes e foco:

- SDLC: backlog executavel Sprint 1 e DoD.
- DBA: contrato snapshot e consistencia.
- Security/Performance: hardening auth e gate pre-release.
- Product Designer e UX Research: KPIs de confianca e validacao assistida.
- Engenharia Normativa: checklist tecnico de Go/No-Go.

#### 3.2 Modelo de checkpoint de convergencia

Checkpoint 48 h:

1. Confirmar inicio das tasks Must have.
2. Validar bloqueadores tecnicos ativos.
3. Revisar risco residual por agente.

Checkpoint D+5:

1. Consolidar evidencias parciais por criterio de aceite.
2. Confirmar estabilidade de rota/auth/snapshot.
3. Atualizar decisao parcial de risco.

Checkpoint D+7:

1. Emitir decisao parcial Go/No-Go.
2. Registrar pendencias e plano de rollback.
3. Definir proxima janela de uso assistido.

#### 3.3 Estados operacionais de governanca

- in_progress: task iniciada com owner e prazo.
- blocked: dependencia critica nao resolvida.
- evidence_pending: implementado sem prova objetiva.
- converged: task concluida com aceite validado.
- release_blocked: criterio critico nao atendido.

#### 3.4 Criterios de aceite testaveis

1. Cada task critica possui dono e prazo explicitos.
2. Cada task possui pelo menos um teste objetivo de validacao.
3. Cada checkpoint possui ata curta com decisao e risco residual.
4. Release permanece bloqueado quando houver `release_blocked` ativo.
5. Decisao Go/No-Go referencia evidencias e nao apenas parecer textual.

#### 3.5 Metricas de governanca

Eventos minimos:

- delegation_created.
- task_status_changed.
- evidence_attached.
- checkpoint_closed.
- release_decision_recorded.

Propriedades minimas:

- agent, task_id, status, blocker_type, evidence_count,
  acceptance_passed, decision, timestamp.

### 4. Responsividade (Desktop, Tablet, Mobile)

Desktop:

- Sem alteracao de layout atual.
- Estados de governanca devem ser legiveis em painels tecnicos existentes.

Tablet:

- Sem alteracao de hierarquia visual.
- Priorizar leitura de status e bloqueadores em area de contexto.

Mobile:

- Sem alterar action bar atual.
- Garantir que mensagens de bloqueio nao ocultem CTA principal.

### 5. Acessibilidade (WCAG 2.1 AA)

Requisitos:

- Estados de governanca com texto explicito e semanticamente claros.
- Leitor de tela deve anunciar mudanca de estado critico.
- Foco visivel em controles de acao e recuperacao.
- Mensagens de bloqueio com linguagem objetiva e acao recomendada.

### 6. Entregaveis ativados

Checklist de handoff aplicado:

- Objetivo, escopo e criterios de sucesso definidos para execucao P4.
- Modelo de checkpoint e estados operacionais documentados.
- Responsividade e acessibilidade mantidas sem mudanca visual.
- Metricas de governanca prontas para monitorar convergencia.

Handoff de desenvolvimento:

1. Publicar template unico de delegacao por agente.
2. Registrar checkpoints 48 h, D+5 e D+7 com evidencias anexadas.
3. Integrar status `release_blocked` ao gate de decisao operacional.
4. Manter decisao Go/No-Go vinculada aos criterios da secao 3.4.

## 15. Especificacao UX/UI - Operacao de Checkpoint e Decisao (P5)

Data de referencia: 2026-03-24.

Escopo: transformar checkpoints D+2, D+5 e D+7
em ciclo operacional padronizado de decisao,
sem alterar interface de produto.

### 1. Objetivo e contexto

Objetivo do usuario:

- Ler rapidamente o status real de execucao por agente.
- Entender se deve avancar, bloquear ou exigir mitigacao.
- Tomar decisao com base em evidencias verificaveis.

Objetivo de negocio:

- Reduzir latencia de decisao no comite PM/Tech Lead.
- Evitar liberacao com risco critico mascarado por opiniao.
- Garantir previsibilidade de entrega dos Must have.

Criterios de sucesso:

- D+2 publicado com bloqueadores claros por trilha.
- D+5 publicado com status objetivo de Must have.
- D+7 publicado com decisao parcial Go/No-Go justificada.

Restricoes:

- Sem mudanca visual do fluxo de calculo.
- Sem flexibilizar gate de paridade LIGHT.
- Sem remover criterio de rastreabilidade minima auditavel.

### 2. Decisoes UX/UI com justificativa

#### 2.1 Sintese antes de detalhe

Decisao:

- Iniciar cada checkpoint por resumo executivo curto
  com decisao atual e condicao de saida.

Justificativa:

- Nielsen: Aesthetic and Minimalist Design.
- Reduz carga cognitiva no momento de decisao.

Impacto esperado:

- Reunioes mais objetivas e com menos retrabalho.

#### 2.2 Evidencia vinculada a criterio

Decisao:

- Cada status deve referenciar criterio objetivo
  e evidencia esperada no mesmo bloco.

Justificativa:

- Nielsen: Recognition rather than Recall.
- Evita discussoes sem base observavel.

Impacto esperado:

- Melhor rastreabilidade entre execucao e decisao.

#### 2.3 Risco residual como gate explicito

Decisao:

- Toda decisao parcial deve trazer risco residual
  com owner e mitigacao ativa.

Justificativa:

- Nielsen: Help users recognize and recover from errors.

Impacto esperado:

- Menos surpresas no momento de liberar escopo critico.

### 3. Especificacao de implementacao

#### 3.1 Estrutura obrigatoria por checkpoint

Cada checkpoint deve conter:

- resumo executivo.
- status por agente.
- bloqueadores.
- must have e aceite.
- decisao parcial Go/No-Go.
- risco residual e mitigacao.
- proximas acoes com prazo relativo.

#### 3.2 Semantica operacional de status

- concluido_para_plano: agente entregou plano validavel.
- em_andamento_execucao: entrega tecnica ainda em implementacao.
- bloqueado: dependencia critica impede avancar.
- pronto_para_decisao: evidencia suficiente para deliberacao.

#### 3.3 Criterios de aceite testaveis

1. D+2 possui status de todos os agentes obrigatorios.
2. D+5 possui lista de Must have com dono e evidencia esperada.
3. D+7 possui regra explicita de Go parcial ou No-Go.
4. Risco residual mapeia pelo menos 4 riscos com owner.
5. Encerramento indica condicao objetiva de continuidade.

#### 3.4 Regras de decisao parcial

- Go parcial apenas com contrato, auth e snapshot sem falha critica.
- No-Go quando qualquer criterio critico estiver em bloqueio.
- Pendencia sem evidencia vira risco aberto com owner nomeado.

#### 3.5 Instrumentacao minima

Eventos minimos:

- checkpoint_published.
- checkpoint_decision_changed.
- must_have_status_changed.
- residual_risk_registered.

Propriedades minimas:

- checkpoint_phase, decision, critical_blockers,
  must_have_open_count, residual_risk_count, timestamp.

### 4. Responsividade (Desktop, Tablet, Mobile)

Desktop:

- Resumo no topo e secoes sequenciais abaixo.
- Leitura prioriza status por agente antes de riscos.

Tablet:

- Mesma ordem informacional do desktop.
- Blocos curtos para leitura em revisao de comite.

Mobile:

- Secoes compactas com titulos curtos e listas objetivas.
- Sem sobreposicao de conteudo critico em mensagens de bloqueio.

### 5. Acessibilidade (WCAG 2.1 AA)

Requisitos:

- Status e decisoes sempre em texto explicito.
- Contraste AA em labels de estado e risco.
- Ordem de leitura consistente por secao.
- Mensagens de bloqueio com acao recomendada clara.

### 6. Entregaveis ativados

Checklist de handoff aplicado:

- Objetivo, escopo e criterio de sucesso definidos.
- Estados operacionais e regra de decisao padronizados.
- Responsividade e WCAG preservados sem mudanca visual.
- Metricas e eventos de checkpoint documentados.

Handoff de desenvolvimento:

1. Manter artefato unico de checkpoint com D+2, D+5 e D+7.
2. Atualizar status por agente em cada janela de revisao.
3. Registrar decisao parcial com risco residual e owner.
4. Bloquear release quando criterio critico estiver aberto.
