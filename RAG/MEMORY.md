# RAG / Memory Baseline - calculo_tracao_light

## Contexto real do projeto

- Stack atual: frontend React + Vite e backend FastAPI em Python.
- Objetivo funcional principal: reproduzir com fidelidade os calculos e comportamentos da planilha LIGHT.
- Fonte de verdade de regra de negocio: workbook Excel (paridade vem antes de otimizacoes teoricas).
- Integracoes externas ficam subordinadas ao custo zero no MVP.
- Escopo atual nao inclui reescrita da logica de calculo sem gap comprovado de paridade.

## Regras ativas (nao negociaveis)

- Fluxo de trabalho principal na branch dev.
- Mesa Redonda Multidisciplinar (protocolo obrigatorio): sempre que um problema envolver mais de uma disciplina, o PM deve interromper o fluxo linear e convocar UX, DBA, Dev e Engenheiro para rodada de pareceres; antes de qualquer codigo, deve explicitar conflitos positivos e fechar com Relatorio de Convergencia contendo Decisao Final, Trade-offs e Plano de Acao por agente.
- Sem dados mockados fora do ambiente de testes.
- UI com abordagem 2.5D (nao 3D), apenas quando fizer sentido de experiencia.
- Modularidade e SRP em backend e frontend.
- Seguranca por padrao em API, dados e automacoes.
- Clean code como criterio de manutencao.
- Arquitetura thin frontend e smart backend.
- Otimizacao orientada a gargalo real e metricas.
- Testes unitarios + E2E para fluxos criticos.
- Sanitizacao de dados de entrada e saida.
- Docker-first para setup local, CI e padronizacao de execucao.
- Interface em pt-BR.
- Zero custo para integracoes externas no MVP.
- Modularizar arquivos com mais de 500 linhas.
- Cobertura alvo: 100% nos 20% fluxos mais criticos e >=80% no restante.
- Governanca normativa operacional obrigatoria para fluxos de calculo e persistencia.
- Bloqueio de liberacao quando faltar evidencia objetiva de paridade LIGHT e rastreabilidade minima auditavel.
- Uso assistido por responsavel tecnico obrigatorio em liberacoes iniciais e mudancas sensiveis de dominio critico.

## Regras removidas/ajustadas por contexto

- Half-way BIM: removida do baseline por estar fora do escopo atual do produto.
- DDD estrito: ajustado para DDD pragmatico, aplicado onde agrega clareza e nao como obrigatoriedade universal.
- Commit automatico ao fim da task: ajustado para executar somente quando solicitado/aprovado no fluxo.

## Mapa de papeis

- Tech Lead orquestrador: define prioridade, escopo, riscos e delegacao entre agentes.
- Dev Fullstack Senior: implementa backend/frontend production-ready mantendo paridade com Excel.
- DevOps/QA: garante pipeline, ambiente Docker, qualidade de release, testes e observabilidade.
- UI/UX: traduz requisitos em experiencia 2.5D consistente, acessivel e em pt-BR.
- Estagiario criativo: gera alternativas acionaveis e prototipos rapidos sem violar restricoes tecnicas.
