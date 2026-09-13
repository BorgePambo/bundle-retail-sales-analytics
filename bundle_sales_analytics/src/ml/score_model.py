"""
Score customers for purchase propensity.

Loads the trained model from MLflow and generates purchase probability scores
for all customers.
"""

import mlflow
import mlflow.spark
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.ml import PipelineModel
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_spark() -> SparkSession:
    """Get or create Spark session."""
    return SparkSession.builder.getOrCreate()

def load_trained_model(model_name: str = "purchase_propensity_model"):
    """
    Load the latest version of the trained model from MLflow registry.
    """
    try:
        model_uri = f"models:/{model_name}/latest"
        model = mlflow.spark.load_model(model_uri)
        logger.info(f"Loaded model: {model_uri}")
        return model
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def load_feature_pipeline(pipeline_path: str = "/tmp/feature_pipeline"):
    """
    Load the feature transformation pipeline.
    """
    pipeline = PipelineModel.load(pipeline_path)
    logger.info(f"Loaded feature pipeline from {pipeline_path}")
    return pipeline

def score_customers(spark: SparkSession, model, pipeline, catalog: str = "retails_sales_dev") -> None:
    """
    Generate purchase propensity scores for all customers.
    """
    from src.ml.features import build_features

    # Load features
    features_df = build_features(spark, catalog=catalog)

    # Apply feature pipeline
    processed_df = pipeline.transform(features_df)

    # Score
    scored_df = model.transform(processed_df)

    # Extract probability score
    scored_df = scored_df.withColumn(
        "purchase_probability",
        F.col("probability").getItem(1)  # Probability of class 1 (will purchase)
    ).select(
        "sk cliente",
        "nome_completo",
        "purchase_probability",
        "prediction"
    )

    # Write scores to gold table
    scored_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(
        f"{catalog}.gold.customer_purchase_scores"
    )

    logger.info(f"Scored {scored_df.count()} customers")

    return scored_df

def main():
    """Main scoring pipeline."""
    spark = get_spark()

    # Set MLflow tracking
    mlflow.set_tracking_uri("databricks")
    mlflow.set_registry_uri("databricks-uc")

    # Load model
    model = load_trained_model()

    # Load pipeline
    pipeline = load_feature_pipeline()

    # Score customers
    scores = score_customers(spark, model, pipeline)

    # Show top 10 customers by purchase probability
    scores.orderBy("purchase_probability", ascending=False).show(10, truncate=False)

    spark.stop()

if __name__ == "__main__":
    main()