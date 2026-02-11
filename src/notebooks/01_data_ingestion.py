# Databricks notebook source
# MAGIC %md
# MAGIC # Data Ingestion Pipeline
# MAGIC Ingests raw data and stores in Delta format

# COMMAND ----------

import pyspark.sql.functions as F
from pyspark.sql import DataFrame
from delta.tables import DeltaTable
from datetime import datetime

# COMMAND ----------

# MAGIC %md
# MAGIC ## Parameters

# COMMAND ----------

dbutils.widgets.text("catalog", "main", "Catalog")
dbutils.widgets.text("schema", "mlops_prod", "Schema")
dbutils.widgets.text("environment", "dev", "Environment")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
environment = dbutils.widgets.get("environment")

print(f"Environment: {environment}")
print(f"Catalog: {catalog}")
print(f"Schema: {schema}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load Raw Data

# COMMAND ----------

# Sample data source - replace with actual source
raw_data_path = f"dbfs:/mnt/raw-data/{environment}/"

df_raw = spark.read \
    .format("parquet") \
    .load(raw_data_path)

print(f"Loaded {df_raw.count():,} rows")
display(df_raw.limit(5))

# COMMAND ----------

# MAGIC %md  
# MAGIC ## Data Quality Checks

# COMMAND ----------

# Check for required columns
required_columns = ["id", "timestamp", "feature1", "feature2", "target"]
missing_columns = set(required_columns) - set(df_raw.columns)

if missing_columns:
    raise ValueError(f"Missing required columns: {missing_columns}")

# Check for nulls
null_counts = df_raw.select([
    F.sum(F.col(c).isNull().cast("int")).alias(c) 
    for c in df_raw.columns
])

display(null_counts)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Transformations

# COMMAND ----------

df_transformed = df_raw \
    .filter(F.col("id").isNotNull()) \
    .dropDuplicates(["id"]) \
    .withColumn("ingestion_timestamp", F.current_timestamp()) \
    .withColumn("ingestion_date", F.current_date()) \
    .withColumn("data_source", F.lit("raw_data"))

print(f"Transformed data: {df_transformed.count():,} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write to Delta Lake

# COMMAND ----------

# Create schema if not exists
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")

# Write to Delta table
target_table = f"{catalog}.{schema}.raw_data"

df_transformed.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .option("mergeSchema", "true") \
    .saveAsTable(target_table)

# Optimize table
spark.sql(f"OPTIMIZE {target_table}")

print(f"Data written to: {target_table}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Return Results

# COMMAND ----------

import json

result = {
    "status": "SUCCESS",
    "rows_ingested": df_transformed.count(),
    "table_name": target_table,
    "timestamp": datetime.now().isoformat()
}

dbutils.notebook.exit(json.dumps(result))
