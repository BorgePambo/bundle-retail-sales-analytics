"""
ML Model Training for Purchase Propensity Prediction.

Trains classification models to predict customer purchase probability
using features from gold.fct_vendas and dimensions.
"""

import mlflow
import mlflow.sklearn
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, lit
from pyspark.ml import Pipeline
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.classification import LogisticRegression, RandomForestClassifier, GBTClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator, MulticlassClassificationEvaluator
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_spark() -> SparkSession:
    """Get or create Spark session."""
    return SparkSession.builder.getOrCreate()

def prepare_training_data(features_df) -> Any:
    """
    Prepare features and label for training.

    Creates a binary label: 1 if customer made >1 purchase in last 3 months,
    0 otherwise (or could be based on recency).
    """
    # For purchase propensity, we'll predict likelihood of future purchase
    # Using recency as proxy: customers who purchased recently are more likely to buy again

    # Create label: 1 if purchased in last 90 days, 0 otherwise
    # Assuming we have a date reference - in real scenario would use current date
    # For demo, we'll use max date in dataset minus 90 days as threshold

    # Actually, let's make it simpler: predict if customer will make another purchase
    # based on their historical behavior - we'll create a synthetic label for demo

    # In real scenario, you'd have a time-based split:
    # - Train on data before date T
    # - Predict purchase in window [T, T+future_window]

    # For now, we'll create a heuristic label based on frequency and recency
    prepared_df = features_df.withColumn(
        "label",
        when(
            (col("total_purchases") > 1) & (col("recency_days") < 60), 1
        ).otherwise(0)
    )

    # Select feature columns (exclude identifiers and target)
    feature_cols = [c for c in prepared_df.columns
                   if c not in ["sk_cliente", "nome_completo", "label", "first_purchase_date", "last_purchase_date"]]

    logger.info(f"Using {len(feature_cols)} features for training")

    # Assemble features vector
    assembler = VectorAssembler(
        inputCols=feature_cols,
        outputCol="features_raw"
    )

    # Scale features
    scaler = StandardScaler(
        inputCol="features_raw",
        outputCol="features",
        withStd=True,
        withMean=False  # Set to False for sparse data compatibility
    )

    # Create pipeline
    pipeline = Pipeline(stages=[assembler, scaler])

    # Fit pipeline
    pipeline_model = pipeline.fit(prepared_df)
    processed_df = pipeline_model.transform(prepared_df)

    return processed_df.select("features", "label"), pipeline_model, feature_cols

def train_models(train_data, test_data) -> Dict[str, Any]:
    """
    Train multiple models and return the best performer.
    """
    models = {
        "logistic_regression": LogisticRegression(featuresCol="features", labelCol="label", maxIter=10),
        "random_forest": RandomForestClassifier(featuresCol="features", labelCol="label", numTrees=10),
        "gbt": GBTClassifier(featuresCol="features", labelCol="label", maxIter=10)
    }

    results = {}
    evaluator_auc = BinaryClassificationEvaluator(labelCol="label", rawPredictionCol="rawPrediction", metricName="areaUnderROC")
    evaluator_accuracy = MulticlassClassificationEvaluator(labelCol="label", predictionCol="prediction", metricName="accuracy")

    for name, model in models.items():
        logger.info(f"Training {name}...")

        # Train model
        trained_model = model.fit(train_data)

        # Make predictions
        predictions = trained_model.transform(test_data)

        # Evaluate
        auc = evaluator_auc.evaluate(predictions)
        accuracy = evaluator_accuracy.evaluate(predictions)

        results[name] = {
            "model": trained_model,
            "auc": auc,
            "accuracy": accuracy,
            "predictions": predictions
        }

        logger.info(f"{name} - AUC: {auc:.4f}, Accuracy: {accuracy:.4f}")

    return results

def log_to_mlflow(model_results: Dict[str, Any], feature_cols: List[str], run_name: str = None):
    """
    Log models, parameters, and metrics to MLflow.
    """
    mlflow.set_experiment("/Shared/retail_sales/purchase_propensity")

    with mlflow.start_run(run_name=run_name) as run:
        # Log parameters
        mlflow.log_param("n_features", len(feature_cols))
        mlflow.log_param("feature_names", str(feature_cols[:10]))  # Log first 10

        # Find best model
        best_model_name = max(model_results.keys(), key=lambda k: model_results[k]["auc"])
        best_result = model_results[best_model_name]

        # Log metrics for all models
        for name, result in model_results.items():
            mlflow.log_metric(f"{name}_auc", result["auc"])
            mlflow.log_metric(f"{name}_accuracy", result["accuracy"])

        # Log best model
        mlflow.sklearn.log_model(
            sk_model=best_result["model"],
            artifact_path="model",
            registered_model_name="purchase_propensity_model"
        )

        # Log best model metrics
        mlflow.log_metric("best_model_auc", best_result["auc"])
        mlflow.log_metric("best_model_accuracy", best_result["accuracy"])
        mlflow.log_param("best_model_name", best_model_name)

        logger.info(f"Best model: {best_model_name} with AUC {best_result['auc']:.4f}")

        return run.info.run_id

def main():
    """
    Main training pipeline.
    """
    # Initialize Spark
    spark = get_spark()

    # Set MLflow tracking
    mlflow.set_tracking_uri("databricks")  # Uses Databricks tracking server
    mlflow.set_registry_uri("databricks-uc")

    # Load features
    from src.ml.features import build_features
    features_df = build_features(spark, catalog="retails_sales_dev")

    logger.info(f"Loaded {features_df.count()} customer records")

    # Prepare data
    processed_data, pipeline_model, feature_cols = prepare_training_data(features_df)

    # Split data
    train_data, test_data = processed_data.randomSplit([0.8, 0.2], seed=42)

    logger.info(f"Training set: {train_data.count()} records")
    logger.info(f"Test set: {test_data.count()} records")

    # Train models
    model_results = train_models(train_data, test_data)

    # Log to MLflow
    run_id = log_to_mlflow(model_results, feature_cols, run_name=f"purchase_prophet_{int(time.time())}")

    logger.info(f"MLflow run ID: {run_id}")

    # Save pipeline model for feature transformation
    pipeline_model.write().overwrite().save("/tmp/feature_pipeline")

    spark.stop()

if __name__ == "__main__":
    main()