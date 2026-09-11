# Prompt 01 — Criação da Camada Bronze

## Objetivo

Criar a tabela **`sales_retail`** na camada **Bronze** do projeto Databricks Asset Bundle **`retail_analytics`**, no ambiente **`dev`**, utilizando **Lakeflow Declarative Pipelines / Declarative Spark** e seguindo boas práticas de arquitetura **Lakehouse / Medallion**.

Nesta etapa, criar **somente a camada Bronze**.

**Não criar tabelas, views, pipelines ou recursos de transformação para Silver ou Gold.**

---

## 1. Contexto do Databricks

* Profile: `claude`
* Host: `https://dbc-f487d229-146e.cloud.databricks.com`
* SQL Warehouse: `def139a716f7f061`
* Databricks Free Edition
* Compute: exclusivamente **Serverless**
* Nunca criar ou configurar clusters.
* Sempre informar explicitamente `--profile claude` nos comandos da CLI.

### Catalog e Schema

```text
Catalog: retails_sales_dev
Schema: retails_sales_dev.bronze
Tabela: retails_sales_dev.bronze.sales_retail
```

### Volume de origem

```text
/Volumes/retails_sales_dev/default/raw/erp/
```

Esse diretório contém o arquivo CSV de vendas proveniente do ERP.

---

# 2. Antes de implementar

Antes de alterar qualquer arquivo:

1. Ler as instruções relevantes existentes em:

   * `.claude/`
   * `CLAUDE.md`
   * `databricks.yml`

2. Inspecionar a estrutura atual do Asset Bundle.

3. Verificar se já existe:

   * catálogo `retails_sales_dev`
   * schema `retails_sales_dev.bronze`
   * pipeline relacionado ao projeto
   * tabela `retails_sales_dev.bronze.sales_retail`

4. **Não recriar, substituir, renomear ou excluir recursos existentes sem necessidade.**

5. Antes de definir o schema da tabela, verificar o conteúdo real do CSV existente no Volume.

---

# 3. Arquivo de origem

Origem:

```text
/Volumes/retails_sales_dev/default/raw/erp/
```

O arquivo contém dados de vendas do ERP.

Colunas observadas:

```text
Data da Venda
Produto
Categoria
PrecoUnitario
Custo Unitário
Marca
Qtd. Vendida
Nome Cliente
Localidade
Unnamed: 9
_rescued_data
```

As principais informações de negócio são:

```text
Data da Venda
Produto
Categoria
Preço Unitário
Custo Unitário
Marca
Quantidade Vendida
Nome Cliente
Localidade
```

---

# 4. Regras da camada Bronze

A tabela Bronze deve representar uma **ingestão técnica do dado de origem**, preservando o máximo possível o conteúdo original.

### Permitido nesta etapa

Realizar somente:

* ingestão do CSV;
* padronização técnica dos nomes das colunas;
* remoção das colunas claramente identificadas como ruído;
* criação da coluna técnica `ingested_timestamp`.

### Não permitido

Não aplicar:

* regras de negócio;
* filtros de registros;
* agregações;
* cálculos de faturamento;
* cálculos de margem;
* cálculos de lucro;
* deduplicação baseada em regra de negócio;
* tratamento analítico;
* enriquecimento;
* joins;
* criação de dimensões;
* criação de fatos;
* transformações próprias da Silver;
* criação de tabelas Silver;
* criação de tabelas Gold.

---

# 5. Padronização das colunas

Normalizar os nomes das colunas para um padrão consistente em `snake_case`.

Mapeamento esperado:

```text
Data da Venda       → data_venda
Produto             → produto
Categoria           → categoria
PrecoUnitario       → preco_unitario
Custo Unitário      → custo_unitario
Marca               → marca
Qtd. Vendida        → quantidade
Nome Cliente        → cliente
Localidade          → localidade
```

A tabela final deverá conter essas colunas.

---

# 6. Colunas de ruído

O arquivo contém:

```text
Unnamed: 9
_rescued_data
```

### `Unnamed: 9`

Essa coluna aparenta ser uma coluna vazia/artefato do arquivo de origem.

Verificar o conteúdo antes da implementação.

Se estiver efetivamente vazia e sem valor operacional, **não incluí-la na tabela Bronze**.

### `_rescued_data`

Essa coluna pode estar relacionada ao mecanismo de rescue utilizado durante a ingestão.

Verificar se existem valores nela.

Se estiver `NULL` em todos os registros e não houver dados resgatados, não é necessário propagá-la para a tabela final.

**Não inventar tratamento para essas colunas.**

O objetivo é somente evitar que colunas claramente artificiais do arquivo contaminem o schema da tabela Bronze.

---

# 7. Coluna técnica de ingestão

Criar:

```text
ingested_timestamp
```

Ela deve representar o timestamp da ingestão do registro no pipeline.

Utilizar uma função nativa de timestamp, como:

```sql
current_timestamp()
```

Essa coluna é **metadado técnico de ingestão**, não regra de negócio.

---

# 8. Implementação

Utilizar **Lakeflow Declarative Pipelines / Declarative Spark**.

A ingestão deve ser implementada como um pipeline declarativo dentro do Asset Bundle.

Preferir mecanismos nativos do Databricks para ingestão de arquivos, como **Auto Loader (`cloudFiles`)**, quando forem compatíveis com a estrutura atual do projeto.

Origem:

```text
/Volumes/retails_sales_dev/default/raw/erp/
```

Destino:

```text
retails_sales_dev.bronze.sales_retail
```

O pipeline deve ser responsável pela criação/atualização da tabela Bronze.

Não utilizar notebook para implementar uma lógica que poderia ser expressa diretamente como pipeline declarativo.

---

# 9. Asset Bundle

Adicionar ou ajustar somente os recursos necessários para executar a ingestão Bronze.

O target deve permanecer:

```yaml
dev:
```

### REGRA CRÍTICA

**NÃO utilizar `mode: development`.**

O uso de `mode: development` pode alterar os nomes dos recursos, inclusive schemas do Unity Catalog, criando nomes como:

```text
dev_<usuario>_bronze
```

Isso quebraria a arquitetura definida para este projeto.

Em vez disso, utilizar explicitamente:

```yaml
presets:
  trigger_pause_status: PAUSED
```

Adicionar um comentário no `databricks.yml` explicando por que `mode: development` não deve ser utilizado neste projeto.

Os nomes dos recursos devem permanecer exatamente:

```text
retails_sales_dev
bronze
sales_retail
```

Não criar prefixos automáticos.

---

# 10. Recursos que NÃO devem ser criados

Nesta etapa NÃO criar:

* clusters;
* SQL Warehouses adicionais;
* schemas Silver;
* schemas Gold;
* tabelas Silver;
* tabelas Gold;
* views Silver;
* views Gold;
* jobs adicionais;
* notebooks desnecessários;
* dashboards;
* Genie;
* Databricks Apps;
* recursos de ML;
* regras de negócio.

Criar somente o necessário para a ingestão da tabela:

```text
retails_sales_dev.bronze.sales_retail
```

---

# 11. Validação

Depois da implementação, executar:

```bash
databricks bundle validate --target dev --profile claude
```

Somente continuar se a validação for concluída com sucesso.

---

# 12. Deploy

Após o `validate` passar:

```bash
databricks bundle deploy --target dev --profile claude
```

---

# 13. Execução do pipeline

Depois do deploy, executar o pipeline utilizando o recurso definido no Bundle.

Primeiro identificar o `pipeline_key` no `databricks.yml`.

A execução deverá seguir o padrão:

```bash
databricks bundle run <pipeline_key> --target dev --profile claude
```

**Não utilizar:**

```bash
databricks bundle deploy --target run
```

`deploy` e `run` são operações diferentes.

---

# 14. Validação final no Databricks

Após a execução do pipeline, verificar:

```sql
SELECT *
FROM retails_sales_dev.bronze.sales_retail
LIMIT 20;
```

Verificar também:

```sql
DESCRIBE TABLE retails_sales_dev.bronze.sales_retail;
```

E validar:

* tabela criada no schema correto;
* nomes das colunas padronizados;
* `ingested_timestamp` preenchido;
* `Unnamed: 9` não propagada caso seja realmente vazia;
* `_rescued_data` não propagada caso esteja completamente `NULL`;
* registros carregados corretamente;
* nenhum recurso Silver ou Gold criado.

---

# Resultado esperado

Ao final desta etapa deve existir:

```text
retails_sales_dev
└── bronze
    └── sales_retail
```

Com estrutura técnica semelhante a:

```text
data_venda
produto
categoria
preco_unitario
custo_unitario
marca
quantidade
cliente
localidade
ingested_timestamp
```

A camada Bronze deve permanecer **simples, rastreável e próxima da origem**, deixando limpeza, qualidade, regras de negócio, modelagem dimensional e enriquecimentos para as próximas camadas.
