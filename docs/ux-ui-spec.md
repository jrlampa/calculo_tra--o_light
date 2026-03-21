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

### Eventos recomendados

- project_created.
- point_confirmed.
- calculation_succeeded.
- calculation_persist_queued.
- calculation_persisted.
- calculation_persist_failed.
- calculation_persist_forbidden.
- undo_triggered.
- undo_applied.
- apaga_clicked.
- apaga_undo_window_opened.

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

A implementacao atual cobre stepper, status duplo e action bar. O requisito de undo precisa do ultimo passo de wiring funcional no APAGA para fechamento completo de produto.
