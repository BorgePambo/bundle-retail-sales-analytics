-- =========================================================
-- ANALYTICS - VENDAS
-- =========================================================


-- =========================================================
-- PRODUTO
-- =========================================================

-- 1. Top 10 produtos por receita
SELECT
  p.produto,
  SUM(f.receita) AS receita_total
FROM gold.fct_vendas f
JOIN gold.dim_produto p
  ON f.sk_produto = p.sk_produto
GROUP BY p.produto
ORDER BY receita_total DESC
LIMIT 10;


-- 2. Top 10 produtos por lucro
SELECT
  p.produto,
  SUM(f.lucro) AS lucro_total
FROM gold.fct_vendas f
JOIN gold.dim_produto p
  ON f.sk_produto = p.sk_produto
GROUP BY p.produto
ORDER BY lucro_total DESC
LIMIT 10;


-- 3. Produtos com maior margem
SELECT
  p.produto,
  SUM(f.receita) AS receita_total,
  SUM(f.lucro) AS lucro_total,
  ROUND(
    SUM(f.lucro) / NULLIF(SUM(f.receita), 0) * 100,
    2
  ) AS margem_percentual
FROM gold.fct_vendas f
JOIN gold.dim_produto p
  ON f.sk_produto = p.sk_produto
GROUP BY p.produto
HAVING SUM(f.receita) > 0
ORDER BY margem_percentual DESC
LIMIT 10;


-- 4. Categoria x faturamento
SELECT
  p.categoria,
  SUM(f.receita) AS faturamento
FROM gold.fct_vendas f
JOIN gold.dim_produto p
  ON f.sk_produto = p.sk_produto
GROUP BY p.categoria
ORDER BY faturamento DESC;


-- 5. Marca x faturamento
SELECT
  p.marca,
  SUM(f.receita) AS faturamento
FROM gold.fct_vendas f
JOIN gold.dim_produto p
  ON f.sk_produto = p.sk_produto
GROUP BY p.marca
ORDER BY faturamento DESC;


-- =========================================================
-- CLIENTE
-- =========================================================

-- 6. Top 10 clientes por receita
SELECT
  c.nome_completo,
  SUM(f.receita) AS receita_total
FROM gold.fct_vendas f
JOIN gold.dim_cliente c
  ON f.sk_cliente = c.sk_cliente
GROUP BY c.nome_completo
ORDER BY receita_total DESC
LIMIT 10;


-- 7. Concentração de receita por cliente
SELECT
  c.nome_completo,
  SUM(f.receita) AS receita_cliente,
  ROUND(
    SUM(f.receita) /
    NULLIF((SELECT SUM(receita) FROM gold.fct_vendas), 0) * 100,
    2
  ) AS participacao_percentual
FROM gold.fct_vendas f
JOIN gold.dim_cliente c
  ON f.sk_cliente = c.sk_cliente
GROUP BY c.nome_completo
ORDER BY receita_cliente DESC;


-- 8. Clientes recorrentes
SELECT
  c.nome_completo,
  COUNT(DISTINCT f.sk_data) AS dias_compra,
  SUM(f.receita) AS receita_total
FROM gold.fct_vendas f
JOIN gold.dim_cliente c
  ON f.sk_cliente = c.sk_cliente
GROUP BY c.nome_completo
HAVING COUNT(DISTINCT f.sk_data) > 1
ORDER BY dias_compra DESC;


-- 9. Ticket médio por cliente
SELECT
  c.nome_completo,
  SUM(f.receita) AS receita_total,
  COUNT(*) AS quantidade_compras,
  ROUND(
    SUM(f.receita) / NULLIF(COUNT(*), 0),
    2
  ) AS ticket_medio
FROM gold.fct_vendas f
JOIN gold.dim_cliente c
  ON f.sk_cliente = c.sk_cliente
GROUP BY c.nome_completo
ORDER BY ticket_medio DESC;


-- =========================================================
-- LOCALIDADE
-- =========================================================

-- 10. Faturamento por país
SELECT
  l.pais,
  SUM(f.receita) AS faturamento
FROM gold.fct_vendas f
JOIN gold.dim_localidade l
  ON f.sk_localidade = l.sk_localidade
GROUP BY l.pais
ORDER BY faturamento DESC;


-- 11. Lucro por continente
SELECT
  l.continente,
  SUM(f.lucro) AS lucro_total
FROM gold.fct_vendas f
JOIN gold.dim_localidade l
  ON f.sk_localidade = l.sk_localidade
GROUP BY l.continente
ORDER BY lucro_total DESC;


-- 12. Margem por localização
SELECT
  l.pais,
  SUM(f.receita) AS receita_total,
  SUM(f.lucro) AS lucro_total,
  ROUND(
    SUM(f.lucro) / NULLIF(SUM(f.receita), 0) * 100,
    2
  ) AS margem_percentual
FROM gold.fct_vendas f
JOIN gold.dim_localidade l
  ON f.sk_localidade = l.sk_localidade
GROUP BY l.pais
HAVING SUM(f.receita) > 0
ORDER BY margem_percentual DESC;


-- =========================================================
-- TEMPO
-- =========================================================

-- 13. Evolução mensal
SELECT
  dt.ano,
  dt.mes,
  dt.nome_mes,
  SUM(f.receita) AS receita_total,
  SUM(f.lucro) AS lucro_total
FROM gold.fct_vendas f
JOIN gold.dim_tempo dt
  ON f.sk_data = dt.sk_data
GROUP BY dt.ano, dt.mes, dt.nome_mes
ORDER BY dt.ano, dt.mes;


-- 14. Sazonalidade por mês
SELECT
  dt.mes,
  dt.nome_mes,
  SUM(f.receita) AS receita_total,
  AVG(f.receita) AS receita_media
FROM gold.fct_vendas f
JOIN gold.dim_tempo dt
  ON f.sk_data = dt.sk_data
GROUP BY dt.mes, dt.nome_mes
ORDER BY dt.mes;


-- 15. Comparação mês a mês (MoM)
WITH vendas_mensais AS (
  SELECT
    dt.ano,
    dt.mes,
    dt.nome_mes,
    SUM(f.receita) AS receita_total
  FROM gold.fct_vendas f
  JOIN gold.dim_tempo dt
    ON f.sk_data = dt.sk_data
  GROUP BY dt.ano, dt.mes, dt.nome_mes
)

SELECT
  ano,
  mes,
  nome_mes,
  receita_total,
  LAG(receita_total) OVER (
    ORDER BY ano, mes
  ) AS receita_mes_anterior,
  ROUND(
    (
      receita_total -
      LAG(receita_total) OVER (ORDER BY ano, mes)
    )
    /
    NULLIF(
      LAG(receita_total) OVER (ORDER BY ano, mes),
      0
    ) * 100,
    2
  ) AS crescimento_mom_percentual
FROM vendas_mensais
ORDER BY ano, mes;