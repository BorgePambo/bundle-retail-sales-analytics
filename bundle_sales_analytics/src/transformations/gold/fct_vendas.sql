CREATE OR REFRESH MATERIALIZED VIEW gold.fct_vendas (

sk_data STRING,

sk_produto STRING,

sk_cliente STRING,

sk_localidade STRING,

quantidade INT,

preco_unitario DECIMAL(10,2),

custo_unitario DECIMAL(10,2),

receita DECIMAL(10,2),

lucro DECIMAL(10,2),

margem_percentual DECIMAL(5,2),

mes INT,

nome_mes STRING,

CONSTRAINT valid_quantidade EXPECT (quantidade IS NOT NULL) ON VIOLATION DROP ROW,

CONSTRAINT quantidade_positiva EXPECT (quantidade > 0) ON VIOLATION DROP ROW,

CONSTRAINT valid_preco EXPECT (preco_unitario >= 0) ON VIOLATION DROP ROW,

CONSTRAINT valid_custo EXPECT (custo_unitario >= 0) ON VIOLATION DROP ROW

)

COMMENT 'Fato Vendas - Star Schema (Materialized View) com mes/nome_mes da dim_tempo'

AS SELECT

dt.sk_data,

md5(CONCAT(
TRIM(s.produto), '|',
TRIM(COALESCE(s.categoria, '')), '|',
TRIM(COALESCE(s.marca, ''))
)) AS sk_produto,

cli.sk_cliente AS sk_cliente,

loc.sk_localidade AS sk_localidade,

s.quantidade,

s.preco_unitario,

s.custo_unitario,

s.receita,

s.lucro,

CASE
WHEN s.receita > 0
THEN CAST((s.lucro / s.receita) * 100 AS DECIMAL(5,2))
ELSE 0.00
END AS margem_percentual,

dt.mes,

dt.nome_mes

FROM silver.sales_retail s

LEFT JOIN gold.dim_tempo dt
ON md5(CAST(s.data_venda AS STRING)) = dt.sk_data

LEFT JOIN gold.dim_cliente cli
ON md5(TRIM(s.nome_completo)) = cli.sk_cliente

LEFT JOIN gold.dim_localidade loc
ON md5(CONCAT(
TRIM(s.pais), '|',
TRIM(s.continente)
)) = loc.sk_localidade;
