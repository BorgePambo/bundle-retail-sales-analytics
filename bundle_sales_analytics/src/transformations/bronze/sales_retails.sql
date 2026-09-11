
CREATE OR REFRESH STREAMING TABLE bronze.sales_retail (
  data_venda DATE,
  produto STRING,
  categoria STRING,
  preco_unitario DOUBLE,
  custo_unitario DOUBLE,
  marca STRING,
  quantidade DOUBLE,
  cliente STRING,
  localidade STRING,
  ingested_timestamp TIMESTAMP
)
COMMENT 'Camada Bronze - ingestão técnica do ERP'
AS SELECT
  CAST(`Data da Venda` AS DATE) AS data_venda,
  `Produto` AS produto,
  `Categoria` AS categoria,
  CAST(`PrecoUnitario` AS DOUBLE) AS preco_unitario,
  CAST(`Custo Unitário` AS DOUBLE) AS custo_unitario,
  `Marca` AS marca,
  CAST(`Qtd. Vendida` AS DOUBLE) AS quantidade,
  `Nome Cliente` AS cliente,
  `Localidade` AS localidade,
  current_timestamp() AS ingested_timestamp
FROM STREAM read_files(
   '/Volumes/retails_sales_dev/default/raw/erp/',
  format => 'csv',
  header => true,
  inferSchema => false,
  schemaHints => '`Data da Venda` DATE, `Produto` STRING, `Categoria` STRING, `PrecoUnitario` DOUBLE, `Custo Unitário` DOUBLE, `Marca` STRING, `Qtd. Vendida` DOUBLE, `Nome Cliente` STRING, `Localidade` STRING'
);