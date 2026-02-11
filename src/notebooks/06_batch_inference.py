# Databricks notebook source
# MAGIC %md
# MAGIC # Batch Inference Pipeline
# MAGIC Performs batch predictions using production model

# COMMAND ----------

import mlflow
import pyspark.sql.functions as F
from pyspark.sql.types import *
import json

# COMMAND ----------

# Parameters
model_name = dbutils.widgets.get("model_name")
model_stage = dbutils.widgets.get("model_stage")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load Model

# COMMAND ----------

model_uri = f"models:/{model_name}/{model_stage}"
print(f"Loading model: {model_uri}")

# Create Spark UDF for model
predict_udf = mlflow.pyfunc.spark_udf(
    spark, 
    model_uri=model_uri,
    result_type=DoubleType()
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load Scoring Data

# COMMAND ----------

scoring_table = f"{catalog}.{schema}.scoring_data"
df_scoring = spark.table(scoring_table)

print(f"Loaded {df_scoring.count():,} rows for scoring")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Apply Model

# COMMAND ----------

# Get feature columns
feature_cols = [c for c in df_scoring.columns if c not in ["customer_id", "timestamp"]]

# Apply model
df_predictions = df_scoring.withColumn(
    "prediction",
    predict_udf(*feature_cols)
)

# Add metadata
df_predictions = df_predictions \
    .withColumn("prediction_timestamp", F.current_timestamp()) \
    .withColumn("model_name", F.lit(model_name)) \
    .withColumn("model_stage", F.lit(model_stage))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Save Predictions

# COMMAND ----------

predictions_table = f"{catalog}.{schema}.batch_predictions"

df_predictions.write \
    .format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .saveAsTable(predictions_table)

print(f"Predictions saved to: {predictions_table}")

# COMMAND ----------

result = {
    "status": "SUCCESS",
    "predictions_count": df_predictions.count(),
    "predictions_table": predictions_table,
    "model_name": model_name,
    "model_stage": model_stage
}

dbutils.notebook.exit(json.dumps(result))
