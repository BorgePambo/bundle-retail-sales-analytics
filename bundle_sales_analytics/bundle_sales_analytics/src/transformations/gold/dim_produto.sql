CREATE OR REFRESH MATERIALIZED VIEW gold.dim_produto (
  sk_produto STRING NOT NULL,
  produto STRING NOT NULL,
  categoria STRING,
  marca STRING,
  data_inicio DATE NOT NULL,
  data_fim DATE,
  registro_atual BOOLEAN NOT NULL DEFAULT TRUE,

  CONSTRAINT pk_produto PRIMARY KEY (sk_produto)
);

-- SCD Tipo 2 com MERGE + hash (executado via pipeline ou notebook)
-- Detecta alterações nos atributos rastreados via hash determinístico
MERGE INTO gold.dim_produto AS target
USING (
  SELECT
    md5(CONCAT(TRIM(produto), '|', TRIM(COALESCE(categoria, '')), '|', TRIM(COALESCE(marca, '')))) AS sk_produto,
    TRIM(produto) AS produto,
    TRIM(categoria) AS categoria,
    TRIM(marca) AS marca,
    MIN(CAST(data_venda AS DATE)) AS data_inicio,
    NULL AS data_fim,
    TRUE AS registro_atual
  FROM silver.sales_retail
  GROUP BY TRIM(produto), TRIM(categoria), TRIM(marca)
) AS source
ON target.sk_produto = source.sk_produto
WHEN NOT MATCHED THEN INSERT (sk_produto, produto, categoria, marca, data_inicio, data_fim, registro_atual)
  VALUES (source.sk_produto, source.produto, source.categoria, source.marca, source.data_inicio, source.data_fim, source.registro_atual);
