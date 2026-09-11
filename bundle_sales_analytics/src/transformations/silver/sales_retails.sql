CREATE OR REFRESH MATERIALIZED VIEW silver.sales_retail (
  data_venda DATE,
  produto STRING,
  categoria STRING,
  marca STRING,
  quantidade INT,
  preco_unitario DECIMAL(10,2),
  custo_unitario DECIMAL(10,2),
  receita DECIMAL(10,2),
  lucro DECIMAL(10,2),
  nome_completo STRING,
  pais STRING,
  continente STRING,
  ingested_timestamp TIMESTAMP,

  CONSTRAINT valid_data_venda EXPECT (data_venda IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT valid_produto EXPECT (produto IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT valid_categoria EXPECT (categoria IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT valid_marca EXPECT (marca IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT valid_quantidade EXPECT (quantidade IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT quantidade_positiva EXPECT (quantidade > 0) ON VIOLATION DROP ROW,
  CONSTRAINT preco_valido EXPECT (preco_unitario >= 0) ON VIOLATION DROP ROW,
  CONSTRAINT custo_valido EXPECT (custo_unitario >= 0) ON VIOLATION DROP ROW
)
AS SELECT
  CAST(data_venda AS DATE) AS data_venda,
  TRIM(produto) AS produto,
  TRIM(categoria) AS categoria,
  TRIM(marca) AS marca,
  CAST(quantidade AS INT) AS quantidade,
  CAST(preco_unitario AS DECIMAL(10, 2)) AS preco_unitario,
  CAST(custo_unitario AS DECIMAL(10, 2)) AS custo_unitario,
  CAST(preco_unitario * quantidade AS DECIMAL(10, 2)) AS receita,
  CAST((preco_unitario * quantidade) -
    (custo_unitario * quantidade) AS DECIMAL(10, 2)) AS lucro,
  CONCAT(SPLIT(cliente, ',')[1], ' ', SPLIT(cliente, ',')[0]) AS nome_completo,
  SPLIT(localidade, ' - ')[0] AS pais,
  SPLIT(localidade, ' - ')[1] AS continente,
  ingested_timestamp
FROM bronze.sales_retail
WHERE quantidade IS NOT NULL
  AND data_venda IS NOT NULL;