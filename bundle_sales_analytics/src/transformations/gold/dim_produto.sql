CREATE OR REFRESH MATERIALIZED VIEW gold.dim_produto (
  sk_produto STRING NOT NULL,
  produto STRING NOT NULL,
  categoria STRING NOT NULL,
  marca STRING NOT NULL,

  CONSTRAINT pk_produto PRIMARY KEY (sk_produto)
)
COMMENT 'Dimensão Produto'
AS SELECT DISTINCT
  MD5(CONCAT(TRIM(produto), '|', TRIM(categoria), '|', TRIM(marca))) AS sk_produto,
  TRIM(produto) AS produto,
  TRIM(categoria) AS categoria,
  TRIM(marca) AS marca
FROM silver.sales_retail
WHERE produto IS NOT NULL
  AND categoria IS NOT NULL
  AND marca IS NOT NULL;
