# Databricks notebook source
# MAGIC %md
# MAGIC # Batch Inference Pipeline
# MAGIC Performs batch predictions using production model

# COMMAND ----------

import json
from datetime import datetime

import mlflow
import pyspark.sql.functions as F
from pyspark.sql.types import DoubleType

# COMMAND ----------

# Parameters
model_name = dbutils.widgets.get("model_name")
model_stage = dbutils.widgets.get("model_stage")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
experiment_path = dbutils.widgets.get("experiment_path")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load Model

# COMMAND ----------

model_uri = f"models:/{model_name}/{model_stage}"
print(f"Loading model: {model_uri}")

# Create Spark UDF for model
predict_udf = mlflow.pyfunc.spark_udf(
    spark, model_uri=model_uri, result_type=DoubleType()
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load Scoring Data

# COMMAND ----------

scoring_table = f"{catalog}.{schema}.scoring_data"
df_scoring = spark.table(scoring_table)

scoring_count = df_scoring.count()
print(f"Loaded {scoring_count:,} rows for scoring")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Apply Model

# COMMAND ----------

# Get feature columns
feature_cols = [
    c for c in df_scoring.columns if c not in ["customer_id", "timestamp"]
]

# Compute baseline feature profile from training features for drift comparison.
feature_table = f"{catalog}.{schema}.ml_features"
if spark.catalog.tableExists(feature_table):
    df_baseline = spark.table(feature_table)
else:
    raise ValueError(f"Baseline feature table not found: {feature_table}")

baseline_exprs = [
    F.avg(F.col(c).cast("double")).alias(c)
    for c in feature_cols
    if c in df_baseline.columns
]
current_exprs = [F.avg(F.col(c).cast("double")).alias(c) for c in feature_cols]

baseline_avg = df_baseline.select(baseline_exprs).collect()[0].asDict()
current_avg = df_scoring.select(current_exprs).collect()[0].asDict()

# Drift score is normalized mean shift per feature.
per_feature_drift = {}
for c in current_avg:
    baseline_value = baseline_avg.get(c)
    current_value = current_avg.get(c)
    if baseline_value is None or current_value is None:
        continue
    denom = max(abs(float(baseline_value)), 1e-6)
    per_feature_drift[c] = (
        abs(float(current_value) - float(baseline_value)) / denom
    )

drift_score = (
    sum(per_feature_drift.values()) / len(per_feature_drift)
    if per_feature_drift
    else 0.0
)
drift_detected = drift_score >= 0.2

# Apply model
df_predictions = df_scoring.withColumn(
    "prediction", predict_udf(*feature_cols)
)

# Add metadata
df_predictions = (
    df_predictions.withColumn("prediction_timestamp", F.current_timestamp())
    .withColumn("prediction_date", F.current_date())
    .withColumn("model_name", F.lit(model_name))
    .withColumn("model_stage", F.lit(model_stage))
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Save Predictions

# COMMAND ----------

predictions_table = f"{catalog}.{schema}.batch_predictions"

if spark.catalog.tableExists(predictions_table):
    df_predictions.write.format("delta").mode("append").option(
        "mergeSchema", "true"
    ).saveAsTable(predictions_table)
else:
    df_predictions.write.format("delta").partitionBy("prediction_date").mode(
        "overwrite"
    ).option("overwriteSchema", "true").option(
        "mergeSchema", "true"
    ).saveAsTable(
        predictions_table
    )

# Optimize prediction table for common query predicates.
spark.sql(f"OPTIMIZE {predictions_table} ZORDER BY (customer_id, timestamp)")

print(f"Predictions saved to: {predictions_table}")

# COMMAND ----------

prediction_count = df_predictions.count()

# Log inference and drift metrics to MLflow.
mlflow.set_experiment(experiment_path)
with mlflow.start_run(
    run_name=f"batch_inference_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
):
    mlflow.log_params(
        {
            "model_name": model_name,
            "model_stage": model_stage,
            "scoring_table": scoring_table,
            "predictions_table": predictions_table,
        }
    )
    mlflow.log_metrics(
        {
            "scoring_count": float(scoring_count),
            "predictions_count": float(prediction_count),
            "drift_score": float(drift_score),
            "drift_detected": 1.0 if drift_detected else 0.0,
        }
    )
    mlflow.log_dict(per_feature_drift, "drift/per_feature_drift.json")

result = {
    "status": "SUCCESS",
    "predictions_count": prediction_count,
    "predictions_table": predictions_table,
    "model_name": model_name,
    "model_stage": model_stage,
    "drift": {
        "score": drift_score,
        "detected": drift_detected,
        "threshold": 0.2,
    },
    "storage_optimization": {
        "partition_by": ["prediction_date"],
        "zorder_by": ["customer_id", "timestamp"],
    },
}

dbutils.notebook.exit(json.dumps(result))
