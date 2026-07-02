# Databricks notebook source
# MAGIC %md
# MAGIC # Data Ingestion Pipeline
# MAGIC Ingests raw data and stores in Delta format

# COMMAND ----------

import pyspark.sql.functions as F
from pyspark.sql import DataFrame
from delta.tables import DeltaTable
from datetime import datetime
import json

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
target_table = f"{catalog}.{schema}.raw_data"

df_raw = spark.read \
    .format("parquet") \
    .load(raw_data_path)

raw_count = df_raw.count()
print(f"Loaded {raw_count:,} rows")
display(df_raw.limit(5))

# COMMAND ----------

# MAGIC %md  
# MAGIC ## Data Quality Checks

# COMMAND ----------

# Data contract for ingestion schema and quality thresholds.
contract = {
    "required_columns": {
        "id": ["string"],
        "timestamp": ["timestamp", "date"],
        "feature1": ["double", "float", "decimal", "int", "bigint", "smallint", "tinyint"],
        "feature2": ["double", "float", "decimal", "int", "bigint", "smallint", "tinyint"],
        "target": ["int", "bigint", "smallint", "tinyint"]
    },
    "max_null_ratio": {
        "id": 0.0,
        "timestamp": 0.0,
        "feature1": 0.2,
        "feature2": 0.2,
        "target": 0.0
    },
    "max_duplicate_ratio": 0.1
}

missing_columns = set(contract["required_columns"].keys()) - set(df_raw.columns)

if missing_columns:
    raise ValueError(f"Missing required columns: {missing_columns}")

# Validate expected types with lightweight compatibility checks.
schema_map = {field.name: field.dataType.simpleString() for field in df_raw.schema.fields}
for column, allowed_types in contract["required_columns"].items():
    actual_type = schema_map[column]
    if not any(actual_type.startswith(t) for t in allowed_types):
        raise ValueError(f"Column '{column}' expected one of {allowed_types} but got '{actual_type}'")

# Check null ratios in one pass.
null_counts_row = df_raw.select([
    F.sum(F.col(c).isNull().cast("int")).alias(c)
    for c in contract["required_columns"].keys()
]).collect()[0]

null_ratio = {
    c: (float(null_counts_row[c]) / raw_count if raw_count > 0 else 0.0)
    for c in contract["required_columns"].keys()
}

for column, max_ratio in contract["max_null_ratio"].items():
    if null_ratio[column] > max_ratio:
        raise ValueError(
            f"Data contract failed for '{column}': null ratio {null_ratio[column]:.4f} exceeds {max_ratio:.4f}"
        )

duplicate_count = raw_count - df_raw.select("id", "timestamp").dropDuplicates().count()
duplicate_ratio = float(duplicate_count) / raw_count if raw_count > 0 else 0.0
if duplicate_ratio > contract["max_duplicate_ratio"]:
    raise ValueError(
        f"Data contract failed: duplicate ratio {duplicate_ratio:.4f} exceeds {contract['max_duplicate_ratio']:.4f}"
    )

display(spark.createDataFrame([(k, v) for k, v in null_ratio.items()], ["column", "null_ratio"]))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Transformations

# COMMAND ----------

# Incremental processing: keep only records newer than the latest processed timestamp.
latest_processed_timestamp = None
if spark.catalog.tableExists(target_table):
    latest_processed_timestamp = spark.table(target_table).agg(F.max("timestamp").alias("max_ts")).collect()[0]["max_ts"]

if latest_processed_timestamp is not None:
    df_raw = df_raw.filter(F.col("timestamp") > F.lit(latest_processed_timestamp))
    print(f"Running incremental ingestion from watermark: {latest_processed_timestamp}")
else:
    print("Running full ingestion (no existing watermark found)")

incremental_raw_count = df_raw.count()
if incremental_raw_count == 0:
    result = {
        "status": "SUCCESS",
        "rows_ingested": 0,
        "table_name": target_table,
        "mode": "incremental",
        "message": "No new records to ingest",
        "timestamp": datetime.now().isoformat()
    }
    dbutils.notebook.exit(json.dumps(result))

df_transformed = df_raw \
    .filter(F.col("id").isNotNull()) \
    .dropDuplicates(["id", "timestamp"]) \
    .withColumn("ingestion_timestamp", F.current_timestamp()) \
    .withColumn("ingestion_date", F.current_date()) \
    .withColumn("data_source", F.lit("raw_data"))

transformed_count = df_transformed.count()
print(f"Transformed data: {transformed_count:,} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write to Delta Lake

# COMMAND ----------

# Create schema if not exists
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")

if spark.catalog.tableExists(target_table):
    delta_target = DeltaTable.forName(spark, target_table)
    delta_target.alias("t").merge(
        df_transformed.alias("s"),
        "t.id = s.id AND t.timestamp = s.timestamp"
    ).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
else:
    df_transformed.write \
        .format("delta") \
    .partitionBy("ingestion_date") \
        .mode("overwrite") \
        .option("overwriteSchema", "true") \
        .option("mergeSchema", "true") \
        .saveAsTable(target_table)

# Optimize table layout for common access paths.
spark.sql(f"OPTIMIZE {target_table} ZORDER BY (id, timestamp)")

print(f"Data written to: {target_table}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Return Results

# COMMAND ----------

result = {
    "status": "SUCCESS",
    "rows_ingested": transformed_count,
    "table_name": target_table,
    "mode": "incremental" if latest_processed_timestamp is not None else "full",
    "quality_gates": {
        "duplicate_ratio": duplicate_ratio,
        "null_ratio": null_ratio
    },
    "storage_optimization": {
        "partition_by": ["ingestion_date"],
        "zorder_by": ["id", "timestamp"]
    },
    "timestamp": datetime.now().isoformat()
}

dbutils.notebook.exit(json.dumps(result))
