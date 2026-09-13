"""
Feature Engineering for Purchase Propensity Model.

Reads from gold.fct_vendas and gold dimension tables to build
customer-level features for purchase probability prediction.
"""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from typing import Optional


def get_spark() -> SparkSession:
    """Get or create Spark session."""
    return SparkSession.builder.getOrCreate()


def load_gold_data(spark: SparkSession, catalog: str = "retails_sales_dev") -> tuple:
    """
    Load all Gold tables from Unity Catalog.

    Returns:
        Tuple of (fct_vendas DataFrame, dim_cliente DataFrame,
                  dim_produto DataFrame, dim_localidade DataFrame, dim_tempo DataFrame)
    """
    fct_vendas = spark.table(f"{catalog}.gold.fct_vendas")
    dim_cliente = spark.table(f"{catalog}.gold.dim_cliente")
    dim_produto = spark.table(f"{catalog}.gold.dim_produto")
    dim_localidade = spark.table(f"{catalog}.gold.dim_localidade")
    dim_tempo = spark.table(f"{catalog}.gold.dim_tempo")

    return fct_vendas, dim_cliente, dim_produto, dim_localidade, dim_tempo


def build_customer_features(fct_vendas) -> None:
    """
    Build customer-level features from the fact table.

    Features:
    - total_purchases: Total number of transactions
    - total_revenue: Sum of all revenue
    - total_quantity: Sum of all quantities
    - avg_ticket: Average revenue per transaction
    - unique_products: Number of unique products bought
    - unique_categories: Number of unique categories
    - recency_days: Days since last purchase (relative to max date in data)
    - frequency: Average purchases per month
    - monetary: Average revenue per purchase
    - category_diversity: Ratio of unique categories to total purchases
    - preferred_category: Most purchased category
    - preferred_marca: Most purchased brand
    - avg_margin: Average margin percentage
    - purchase_velocity: Trend of purchases over time (slope)
    - weekday_preference: Preferred day of week for purchases
    - is_weekend_buyer: Whether customer buys on weekends
    """

    # Window for computing recency
    max_date = fct_vendas.agg(F.max("sk_data")).collect()[0][0]

    # Basic aggregations per customer
    customer_features = fct_vendas.groupBy("sk_cliente").agg(
        F.count("*").alias("total_purchases"),
        F.sum("receita").alias("total_revenue"),
        F.sum("quantidade").alias("total_quantity"),
        F.avg("receita").alias("avg_ticket"),
        F.countDistinct("sk_produto").alias("unique_products"),
        F.countDistinct("sk_produto").alias("unique_products_count"),
        F.max("sk_data").alias("last_purchase_date"),
        F.min("sk_data").alias("first_purchase_date"),
        F.avg("margem_percentual").alias("avg_margin"),
        F.sum("lucro").alias("total_profit"),
    )

    # Add derived features
    customer_features = customer_features.withColumn(
        "recency_days",
        F.datediff(F.lit(max_date), F.col("last_purchase_date"))
    ).withColumn(
        "customer_lifetime_days",
        F.datediff(F.col("last_purchase_date"), F.col("first_purchase_date"))
    ).withColumn(
        "avg_monthly_purchases",
        F.when(
            F.col("customer_lifetime_days") > 0,
            F.col("total_purchases") / (F.col("customer_lifetime_days") / 30.0)
        ).otherwise(F.col("total_purchases"))
    ).withColumn(
        "category_diversity",
        F.when(
            F.col("total_purchases") > 0,
            F.col("unique_products_count") / F.col("total_purchases")
        ).otherwise(0)
    )

    return customer_features


def add_product_category_features(fct_vendas, customer_features) -> None:
    """
    Add product and category preference features.
    """
    # Preferred category per customer
    pref_category = fct_vendas.groupBy("sk_cliente", "sk_produto").agg(
        F.sum("receita").alias("produto_receita"),
        F.count("*").alias("produto_compras")
    )

    # Join back to get category info would require dim_produto
    # For now, aggregate by customer-level category preferences
    category_pref = fct_vendas.groupBy("sk_cliente").agg(
        F.countDistinct("sk_produto").alias("n_categories_visited"),
    )

    customer_features = customer_features.join(category_pref, on="sk_cliente", how="left")

    return customer_features


def add_temporal_features(fct_vendas, customer_features) -> None:
    """
    Add temporal purchasing patterns.
    """
    # Add month feature for seasonal analysis
    temporal = fct_vendas.groupBy("sk_cliente", "mes").agg(
        F.count("*").alias("purchases_this_month"),
        F.sum("receita").alias("revenue_this_month")
    )

    # Pivot to get monthly purchase counts
    monthly_pivot = temporal.groupBy("sk_cliente").agg(
        F.avg("purchases_this_month").alias("avg_purchases_per_month"),
        F.stddev("purchases_this_month").alias("std_purchases_per_month")
    )

    customer_features = customer_features.join(monthly_pivot, on="sk_cliente", how="left")

    return customer_features


def build_features(spark: SparkSession, catalog: str = "retails_sales_dev") -> None:
    """
    Main function to build all customer features.

    Returns a DataFrame ready for ML training.
    """
    fct_vendas, dim_cliente, dim_produto, dim_localidade, dim_tempo = load_gold_data(spark, catalog)

    # Build base customer features
    features_df = build_customer_features(fct_vendas)

    # Add product features
    features_df = add_product_category_features(fct_vendas, features_df)

    # Add temporal features
    features_df = add_temporal_features(fct_vendas, features_df)

    # Join with dim_cliente for additional info
    features_df = features_df.join(dim_cliente.select("sk_cliente", "nome_completo"), on="sk_cliente", how="left")

    # Clean up nulls
    features_df = features_df.fillna(0)

    return features_df


if __name__ == "__main__":
    spark = get_spark()
    features = build_features(spark)
    features.printSchema()
    features.show(20, truncate=False)
