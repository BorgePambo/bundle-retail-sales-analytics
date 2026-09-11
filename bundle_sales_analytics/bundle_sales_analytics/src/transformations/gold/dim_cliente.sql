CREATE OR REFRESH MATERIALIZED VIEW gold.dim_cliente (
  sk_cliente STRING NOT NULL,
  nome_cliente STRING NOT NULL,
  data_inicio DATE NOT NULL,
  data_fim DATE,
  registro_atual BOOLEAN NOT NULL DEFAULT TRUE,

  CONSTRAINT pk_cliente PRIMARY KEY (sk_cliente)
);

MERGE INTO gold.dim_cliente AS target
USING (
  SELECT
    md5(TRIM(nome_completo)) AS sk_cliente,
    TRIM(nome_completo) AS nome_cliente,
    MIN(CAST(data_venda AS DATE)) AS data_inicio,
    NULL AS data_fim,
    TRUE AS registro_atual
  FROM silver.sales_retail
  WHERE TRIM(nome_completo) IS NOT NULL
  GROUP BY TRIM(nome_completo)
) AS source
ON target.sk_cliente = source.sk_cliente
WHEN NOT MATCHED THEN INSERT (sk_cliente, nome_cliente, data_inicio, data_fim, registro_atual)
  VALUES (source.sk_cliente, source.nome_cliente, source.data_inicio, source.data_fim, source.registro_atual);
