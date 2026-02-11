# Databricks notebook source
# MAGIC %md
# MAGIC # Feature Engineering Pipeline
# MAGIC Creates ML features from raw data

# COMMAND ----------

import pyspark.sql.functions as F
from pyspark.sql import Window
from pyspark.sql.types import *

# COMMAND ----------

# Get parameters
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load Raw Data

# COMMAND ----------

raw_table = f"{catalog}.{schema}.raw_data"
df = spark.table(raw_table)

print(f"Loaded {df.count():,} rows from {raw_table}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Feature Creation

# COMMAND ----------

# Aggregate features
window_spec = Window.partitionBy("customer_id").orderBy("timestamp")

df_features = df \
    .withColumn("days_since_last_event", 
                F.datediff(F.current_date(), F.col("timestamp"))) \
    .withColumn("event_count", F.count("*").over(window_spec)) \
    .withColumn("avg_amount", F.avg("amount").over(window_spec)) \
    .withColumn("total_amount", F.sum("amount").over(window_spec)) \
    .withColumn("max_amount", F.max("amount").over(window_spec)) \
    .withColumn("min_amount", F.min("amount").over(window_spec))

# Statistical features
df_features = df_features \
    .withColumn("amount_std", F.stddev("amount").over(window_spec)) \
    .withColumn("amount_variance", 
                F.col("amount_std") / (F.col("avg_amount") + 1))

# Categorical encoding
df_features = df_features \
    .withColumn("category_encoded", 
                F.when(F.col("category") == "A", 1)
                 .when(F.col("category") == "B", 2)
                 .otherwise(0))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Feature Selection

# COMMAND ----------

feature_columns = [
    "customer_id",
    "days_since_last_event",
    "event_count",
    "avg_amount",
    "total_amount",
    "max_amount",
    "min_amount",
    "amount_std",
    "amount_variance",
    "category_encoded",
    "target"
]

df_final = df_features.select(feature_columns)

# Remove nulls
df_final = df_final.na.drop()

print(f"Final features: {df_final.count():,} rows, {len(feature_columns)} columns")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Save Features

# COMMAND ----------

features_table = f"{catalog}.{schema}.ml_features"

df_final.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable(features_table)

print(f"Features saved to: {features_table}")

# COMMAND ----------

import json

result = {
    "status": "SUCCESS",
    "features_table": features_table,
    "feature_count": len(feature_columns),
    "row_count": df_final.count()
}

dbutils.notebook.exit(json.dumps(result))
