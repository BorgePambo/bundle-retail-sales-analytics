# Manual ML Instructions for Purchase Propensity Model

## Overview

This ML solution predicts the probability of purchase for customers based on their historical sales data from the Gold layer.

## Project Structure

```
bundle_sales_analytics/
├── src/
│   ├── transformations/          # Existing Bronze/Silver/Gold SQL layers
│   │   ├── bronze/sales_retails.sql
│   │   ├── silver/sales_retails.sql
│   │   └── gold/
│   │       ├── fct_vendas.sql
│   │       ├── dim_cliente.sql
│   │       ├── dim_produto.sql
│   │       ├── dim_localidade.sql
│   │       └── dim_tempo.sql
│   └── ml/                      # NEW: Machine Learning module
│       ├── features.py          # Feature engineering
│       ├── train_model.py       # Model training script
│       ├── score_model.py       # Model scoring script
│       ├── requirements.txt     # Python dependencies
│       └── notebooks/
│           └── ml_pipeline.ipynb # Interactive notebook
└── resources/
    └── pipeline.yml             # Updated with ML job
```

## Data Sources

**Gold Tables Used:**
- `gold.fct_vendas`: Fact table with sales data (receita, lucro, quantidade, margem_percentual)
- `gold.dim_cliente`: Customer dimension (sk_cliente, nome_completo)
- `gold.dim_produto`: Product dimension
- `gold.dim_localidade`: Location dimension
- `gold.dim_tempo`: Time dimension

## Features Engineered

From `fct_vendas`, the following customer-level features are computed:

| Feature | Description |
|---------|-------------|
| `total_purchases` | Total number of transactions |
| `total_revenue` | Sum of all revenue |
| `total_quantity` | Sum of quantities purchased |
| `avg_ticket` | Average revenue per transaction |
| `unique_products` | Number of unique products bought |
| `recency_days` | Days since last purchase |
| `customer_lifetime_days` | Customer's active period |
| `avg_monthly_purchases` | Purchases per month |
| `category_diversity` | Product diversity ratio |
| `avg_margin` | Average profit margin |

**Target Variable (Label):**
- `label = 1`: Active customer (purchased >1 times and within last 60 days)
- `label = 0`: At-risk customer

## Models Trained

1. **Logistic Regression** - Linear baseline
2. **Random Forest** - Ensemble with feature importance
3. **Gradient Boosted Trees (GBT)** - Sequential ensemble

## MLflow Tracking

- **Experiment**: `/Shared/retail_sales/purchase_propensity`
- **Model Registry**: `purchase_propensity_model`
- **Tracking URI**: `databricks`
- **Registry URI**: `databricks-uc`

## How to Run

### Option 1: Run via Databricks Pipelines Bundle

```bash
# Deploy the bundle (the new job will be included)
databricks bundle deploy -t dev --profile <profile>

# Run the ML training job
databricks bundles run ml_training_job -t dev --profile <profile>
```

### Option 2: Run interactively in Databricks

1. Open the notebook: `/Workspace/Shared/bundle_sales_analytics/src/ml/notebooks/ml_pipeline.ipynb`
2. Run all cells to:
   - Load data from Gold tables
   - Engineer features
   - Train and evaluate 3 models
   - Log results to MLflow
   - Score all customers
   - Save scores to `gold.customer_purchase_scores`

### Option 3: Run via Python scripts

```python
# In Databricks Python notebook or job:
import sys
sys.path.append('/Workspace/Shared/bundle_sales_analytics/src')

from ml.features import build_features
from ml.train_model import main as train_main

# Run training
train_main()
```

## Output Tables

**New table created:**

```sql
-- gold.customer_purchase_scores
SELECT * FROM gold.customer_purchase_scores
ORDER BY purchase_probability DESC;
```

Columns:
- `sk_cliente` - Customer surrogate key
- `nome_completo` - Customer name
- `label` - Ground truth (active/inactive)
- `prediction` - Predicted class
- `purchase_probability` - Probability of being an active customer (0-1)

## Monitoring

View model performance in:
1. MLflow UI: `Experiments > /Shared/retail_sales/purchase_propensity`
2. Model Registry: `Models > purchase_propensity_model`

## Next Steps

1. **Model Retraining**: Set up a recurring job to retrain weekly/monthly
2. **Feature Store**: Consider using Databricks Feature Store for production features
3. **Threshold Tuning**: Adjust classification threshold based on business needs
4. **A/B Testing**: Deploy model to serve recommendations for new customers
5. **Feedback Loop**: Store actual purchases to improve labels for next training