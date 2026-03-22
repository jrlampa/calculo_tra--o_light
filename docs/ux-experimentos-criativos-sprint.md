# Experimentos Criativos de UX/Fluxo - Proxima Sprint

Data: 2026-03-22
Escopo: discovery de baixo risco no fluxo Projeto -> Ponto -> Calculo -> Persistencia.
Premissa: sem alteracao de logica de calculo e sem quebra de paridade com workbook LIGHT.

## 1) Radar de Confianca de Persistencia

Ideia:
- Exibir um mini-indicador textual de confianca no header com 3 niveis: "Pronto para salvar", "Instavel", "Requer acao".
- O nivel usa apenas sinais existentes (saving/queued/error/saved), sem nova regra de negocio.

Metrica de sucesso:
- Reduzir cliques de retry redundantes em 20%.
- Aumentar taxa de "saved" sem retry manual em 10%.

Custo: baixo
Risco: baixo

## 2) Proximo Passo Inteligente

Ideia:
- Adicionar microcopy contextual ao lado do CTA principal com uma frase de proxima acao.
- Exemplo: "Confirme o ponto para habilitar salvamento" ou "Salvo. Pode avancar para o proximo ponto".

Metrica de sucesso:
- Reduzir tempo medio entre "point_confirmed" e "persistence_saved" em 15%.

Custo: baixo
Risco: baixo

## 3) Modo Campo (Foco em Mobile)

Ideia:
- Criar um modo de foco visual opcional para mobile, reduzindo ruido e destacando apenas: estado atual + 2 CTAs principais.
- Ativacao por toggle local (sem persistencia remota).

Metrica de sucesso:
- Reduzir abandonos no mobile antes de "point_confirmed" em 12%.
- Aumentar task success rate mobile em 8%.

Custo: medio
Risco: medio

## 4) Recompensa Progressiva por Ponto

Ideia:
- Exibir feedback progressivo discreto ao salvar pontos consecutivos (ex.: "3 pontos salvos sem erro").
- Sem gamificacao invasiva; foco em confianca operacional.

Metrica de sucesso:
- Aumentar numero medio de pontos persistidos por sessao em 10%.

Custo: baixo
Risco: baixo

## 5) Laboratorio de Mensagens (A/B Local)

Ideia:
- Rodar experimento A/B local para 2 variantes de microcopy de erro de persistencia.
- Variante A: mais tecnica; variante B: mais orientada a acao.

Metrica de sucesso:
- Melhor variante reduz retries sem sucesso em 15%.
- Melhor variante reduz tempo ate recuperacao de erro em 10%.

Custo: baixo
Risco: baixo

## Recomendacao para MVP de zero custo

Executar primeiro os experimentos 1, 2 e 5 somente com:
- textos novos,
- mapeamento de estado ja existente,
- instrumentacao local via console.info("[ux-funnel]").

Nao exige mudanca de API, banco ou formula.

## Spike tecnico sugerido (1 dia)

Objetivo:
- Validar qual microcopy reduz mais retrabalho entre queued/error/saved.

Plano:
1. Aplicar flag local para alternar variante de texto.
2. Instrumentar eventos: persist_retry_manual, persistence_failed, persistence_saved.
3. Medir em ambiente interno por 3-5 dias.
4. Consolidar decisao da variante vencedora para rollout.
