CREATE OR REFRESH MATERIALIZED VIEW gold.dim_localidade (
  sk_localidade STRING NOT NULL,
  pais STRING NOT NULL,
  continente STRING NOT NULL,

  CONSTRAINT pk_localidade PRIMARY KEY (sk_localidade)
)
COMMENT 'Dimensão Localidade'
AS SELECT
  md5(CONCAT(TRIM(pais), '|', TRIM(continente))) AS sk_localidade,
  TRIM(pais) AS pais,
  TRIM(continente) AS continente
FROM (SELECT DISTINCT TRIM(pais) AS pais, TRIM(continente) AS continente FROM silver.sales_retail WHERE pais IS NOT NULL AND continente IS NOT NULL);
