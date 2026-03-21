# Checklist de QA Frontend

## Escopo da rodada
- Fluxo crítico: Projeto -> Ponto -> Cálculo -> Persistência.
- Cobertura: acessibilidade, responsividade, estados de UI, fallback de config, fluxo contínuo ponto a ponto e regressão visual.
- Premissa: sem alteração de fórmula; paridade funcional com workbook permanece.

## 1) Acessibilidade
- [ ] Campo Projeto recebe foco inicial ao abrir a tela de cadastro.
- [ ] Enter submete formulário inicial sem limpar os dados já digitados.
- [ ] Em erro de validação/submissão do projeto, o input Projeto fica com aria-invalid=true.
- [ ] Mensagem de erro do projeto está associada ao input via aria-describedby.
- [ ] Em caso de erro no cadastro, o foco retorna automaticamente para Projeto.
- [ ] Inputs do cabeçalho possuem nome acessível programático por associação label + input.
- [ ] Mensagem de status do cabeçalho possui id estável e pode ser referenciada.
- [ ] Inputs/selects das seções técnicas leem nome composto: campo + travessia + seção.
- [ ] Inputs textuais das seções técnicas usam inputMode decimal.
- [ ] Canvas do relógio mantém aria-label e apresenta resumo textual equivalente em pt-BR.
- [ ] Diagrama do poste está em estrutura semântica figure/figcaption com descrição vinculada.
- [ ] `FlowStepper` é navegável por teclado e anuncia etapa atual para tecnologias assistivas.
- [ ] `HeaderStatusDuplo` expõe dois `role=status` independentes (vínculo e persistência).
- [ ] Botão "Tentar novamente" da persistência é acionável por teclado e leitor de tela.

## 2) Responsividade e toque
- [ ] Desktop >= 961px mantém layout em duas colunas sem quebra visual.
- [ ] Tablet/mobile <= 960px empilha conteúdo sem ocultar informações críticas.
- [ ] Em pointer coarse, botões principais possuem alvo mínimo de 44px.
- [ ] Em pointer coarse, APAGA, seletores de poste e inputs-chave do header/projeto possuem alvo mínimo de 44px.
- [ ] Ajustes mobile não degradam alinhamento e densidade da versão desktop.
- [ ] Mobile <= 767px mantém `ActionBar` fixa sem cobrir conteúdo (padding bottom ajustado).
- [ ] `UndoToast` aparece acima da `ActionBar` fixa e não bloqueia campos críticos.

## 3) Estados de UI
- [ ] Config inicia em idle e transita para loading automaticamente ao montar App.
- [ ] Banner de loading de config aparece acima dos selects de poste.
- [ ] Em erro de config, banner visível mostra mensagem em pt-BR e botão Tentar novamente.
- [ ] Retry de config executa nova tentativa sem limpar último config válido.
- [ ] Se tipo do poste mudar, modelo é limpo imediatamente.
- [ ] Helper text de Modelo do Poste está visível e associado por aria-describedby.
- [ ] Estados de ponto/persistência seguem feedback no cabeçalho (idle/saving/saved/error).
- [ ] Persistência em retry automático mostra countdown "Tentando em Xs...".
- [ ] Após 3 tentativas falhas, persistência mostra erro estável com retry manual.
- [ ] Falha `403/42501` de persistência aparece como erro de acesso/ownership, sem retry automático indevido.
- [ ] Erro 422 de domínio aparece no campo específico (não apenas em banner global).
- [ ] Stepper reflete transição correta: Projeto -> Ponto -> Cálculo -> Persistido.
- [ ] Após persistência `saved`, CTA "Próximo ponto" fica disponível sem recarregar contexto do projeto.

## 4) APAGA com desfazer
- [ ] Acionar APAGA abre `UndoToast` com janela de 5s.
- [ ] Durante a janela, campos ainda não são limpos definitivamente.
- [ ] Clicar "Desfazer" restaura estado integral sem perda de foco.
- [ ] Após timeout, limpeza afeta apenas dados técnicos do ponto atual (não limpa dados do projeto).

## 5) Fallback de /api/config
- [ ] Cenário sucesso inicial: selects populam com dados normalizados.
- [ ] Cenário payload parcial/inválido: app não quebra e aplica arrays/objetos vazios com segurança.
- [ ] Cenário falha após sucesso: UI mantém dados válidos anteriores e apenas atualiza status para erro.
- [ ] Cenário retry bem-sucedido: status retorna para success e mantém continuidade do fluxo.

## 6) Regressão visual
- [ ] Visual Excel-like e 2.5D permanece consistente em painel, header, tabelas e botões.
- [ ] Tabela técnica continua com estrutura T1..T4 sem alteração de geometria.
- [ ] Diagrama do poste não teve alteração geométrica (apenas semântica).
- [ ] Relógio de ângulos mantém desenho e contraste dos vetores/resultante.
- [ ] Chips de status (vínculo/persistência) mantêm contraste AA em estado normal e erro.

## 7) Fluxo ponta a ponta (Projeto -> Ponto -> Persistência)
- [ ] Usuário consegue criar projeto com dados comuns e navegar para etapa de cálculo.
- [ ] Usuário preenche ponto + tipo/modelo, confirma ponto e recebe status claro.
- [ ] Usuário altera ponto/tipo/modelo e vínculo anterior é invalidado corretamente.
- [ ] Resultado total e seções atualizam sem perda de foco involuntária.
- [ ] Persistência comunica saving/queued/saved/error sem silêncio de falha.
- [ ] Persistência diferencia erro transitório de erro de autorização sem colapsar ambos no mesmo texto.
- [ ] Loop operacional funciona: salvar ponto atual -> avançar para "Próximo ponto" mantendo contexto do projeto.

## 8) Critérios de saída da QA
- [ ] Sem erros de diagnóstico estático nos arquivos alterados.
- [ ] Sem regressão funcional nos testes E2E críticos existentes.
- [ ] E2E sem mocks do backend validado em ambiente integrado ao menos para 1 cenário feliz e 1 cenário de falha de persistência.
- [ ] Não há bloqueio A11y de severidade alta no fluxo crítico.
- [ ] Sem bloqueio de fallback para indisponibilidade de /api/config.
