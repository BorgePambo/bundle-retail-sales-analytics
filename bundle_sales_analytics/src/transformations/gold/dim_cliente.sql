CREATE OR REFRESH MATERIALIZED VIEW gold.dim_cliente (
  sk_cliente STRING NOT NULL,
  nome_completo STRING NOT NULL,

  CONSTRAINT pk_cliente PRIMARY KEY (sk_cliente)
)
COMMENT 'Dimensão Cliente'
AS SELECT DISTINCT
  MD5(TRIM(nome_completo)) AS sk_cliente,
  TRIM(nome_completo) AS nome_completo
FROM silver.sales_retail
WHERE nome_completo IS NOT NULL;
