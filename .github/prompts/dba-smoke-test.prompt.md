---
description: "Smoke test rapido para o agente Database Architect and DBA Senior — valida SQL Tuning, Migration e Cache com 3 comandos"
tools: [read, search]
agent: "Database Architect and DBA Senior"
---
Execute os 3 comandos abaixo em sequencia para validar as habilidades principais do agente DBA. Use o banco de dados do projeto atual (assumir PostgreSQL se nao especificado).

## Comando 1 — SQL Tuning
Analise a query abaixo e entregue: diagnostico de execucao (identificar Seq Scan, sorts caros, join problems), proposta de reescrita otimizada e sugestao de indices com justificativa.

```sql
SELECT u.id, u.nome, COUNT(p.id) AS total_pedidos, SUM(p.valor) AS total_valor
FROM usuarios u
LEFT JOIN pedidos p ON p.usuario_id = u.id
WHERE u.ativo = true
  AND p.criado_em >= NOW() - INTERVAL '90 days'
GROUP BY u.id, u.nome
ORDER BY total_valor DESC;
```

---

## Comando 2 — Schema Migration (CI/CD-ready)
Gere a migracao Up e Down para adicionar a coluna `preferencias JSONB DEFAULT '{}'::jsonb` na tabela `usuarios`, garantindo zero downtime em tabela de grande volume (> 10 milhoes de linhas). Inclua estrategia anti-lock, plano de rollout e riscos.

---

## Comando 3 — Cache com Redis
Proponha uma estrategia de cache Redis (Cache-Aside) para a query do Comando 1. Inclua: estrutura de chave, TTL recomendado, politica de invalidacao, impacto em consistencia e criterio para decidir entre cache local (in-memory) vs Redis distribuido.
