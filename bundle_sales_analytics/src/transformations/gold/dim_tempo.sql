CREATE OR REFRESH MATERIALIZED VIEW gold.dim_tempo (
  sk_data STRING NOT NULL,
  data_id DATE NOT NULL,
  dia INT NOT NULL,
  mes INT NOT NULL,
  ano INT NOT NULL,
  trimestre INT NOT NULL,
  nome_mes STRING NOT NULL,

  CONSTRAINT pk_tempo PRIMARY KEY (sk_data)
)
COMMENT 'Dimensão Tempo com mês por extenso em português'
AS SELECT
  md5(CAST(data_venda AS STRING)) AS sk_data,
  CAST(data_venda AS DATE) AS data_id,
  DAY(data_venda) AS dia,
  MONTH(data_venda) AS mes,
  YEAR(data_venda) AS ano,
  QUARTER(data_venda) AS trimestre,
  CASE MONTH(data_venda)
    WHEN 1 THEN 'Janeiro'
    WHEN 2 THEN 'Fevereiro'
    WHEN 3 THEN 'Março'
    WHEN 4 THEN 'Abril'
    WHEN 5 THEN 'Maio'
    WHEN 6 THEN 'Junho'
    WHEN 7 THEN 'Julho'
    WHEN 8 THEN 'Agosto'
    WHEN 9 THEN 'Setembro'
    WHEN 10 THEN 'Outubro'
    WHEN 11 THEN 'Novembro'
    WHEN 12 THEN 'Dezembro'
  END AS nome_mes
FROM (SELECT DISTINCT data_venda FROM silver.sales_retail WHERE data_venda IS NOT NULL);
