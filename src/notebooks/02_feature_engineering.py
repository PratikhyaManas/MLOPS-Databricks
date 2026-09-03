# Databricks notebook source
# MAGIC %md
# MAGIC # Feature Engineering Pipeline
# MAGIC Creates ML features from raw data

# COMMAND ----------

import pyspark.sql.functions as F
from delta.tables import DeltaTable
from pyspark.sql import Window
from pyspark.sql.types import DoubleType, StringType

# COMMAND ----------

# Get parameters
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load Raw Data

# COMMAND ----------

raw_table = f"{catalog}.{schema}.raw_data"
features_table = f"{catalog}.{schema}.ml_features"
df = spark.table(raw_table)

raw_count = df.count()
print(f"Loaded {raw_count:,} rows from {raw_table}")

feature_contract = {
    "required_columns": [
        "customer_id",
        "timestamp",
        "amount",
        "category",
        "target",
    ],
    "allowed_categories": ["A", "B"],
    "amount_min": 0.0,
    "max_null_ratio": 0.2,
}

missing_columns = set(feature_contract["required_columns"]) - set(df.columns)
if missing_columns:
    raise ValueError(
        f"Missing required columns for feature engineering: {missing_columns}"
    )

latest_feature_ts = None
if spark.catalog.tableExists(features_table):
    latest_feature_ts = (
        spark.table(features_table)
        .agg(F.max("source_timestamp").alias("max_ts"))
        .collect()[0]["max_ts"]
    )

if latest_feature_ts is not None:
    df = df.filter(F.col("timestamp") > F.lit(latest_feature_ts))
    print(
        f"Running incremental feature engineering from watermark: {latest_feature_ts}"
    )
else:
    print("Running full feature engineering (no existing watermark found)")

incremental_count = df.count()
if incremental_count == 0:
    import json

    result = {
        "status": "SUCCESS",
        "features_table": features_table,
        "feature_count": 0,
        "row_count": 0,
        "mode": "incremental",
        "message": "No new rows to feature-engineer",
    }
    dbutils.notebook.exit(json.dumps(result))

null_ratio_row = df.select(
    [
        F.avg(F.col(c).isNull().cast("double")).alias(c)
        for c in feature_contract["required_columns"]
    ]
).collect()[0]

null_ratio = {
    c: float(null_ratio_row[c]) for c in feature_contract["required_columns"]
}
for col_name, ratio in null_ratio.items():
    if ratio > feature_contract["max_null_ratio"]:
        raise ValueError(
        f"Feature contract failed for '{col_name}': null ratio "
        f"{ratio:.4f} exceeds {feature_contract['max_null_ratio']:.4f}"

invalid_amount_count = df.filter(
    F.col("amount") < F.lit(feature_contract["amount_min"])
).count()
if invalid_amount_count > 0:
    raise ValueError(
        f"Feature contract failed: found {invalid_amount_count} rows with negative amount"
    )

invalid_category_count = df.filter(
    ~F.col("category").isin(feature_contract["allowed_categories"])
).count()
if invalid_category_count > 0:
    raise ValueError(
        f"Feature contract failed: found {invalid_category_count} rows with invalid category values"
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Feature Creation

# COMMAND ----------

# Aggregate features
window_spec = Window.partitionBy("customer_id").orderBy("timestamp")

df_features = (
    df.withColumn("source_timestamp", F.col("timestamp"))
    .withColumn(
        "days_since_last_event",
        F.datediff(F.current_date(), F.col("timestamp")),
    )
    .withColumn("event_count", F.count("*").over(window_spec))
    .withColumn("avg_amount", F.avg("amount").over(window_spec))
    .withColumn("total_amount", F.sum("amount").over(window_spec))
    .withColumn("max_amount", F.max("amount").over(window_spec))
    .withColumn("min_amount", F.min("amount").over(window_spec))
)

# Statistical features
df_features = df_features.withColumn(
    "amount_std", F.stddev("amount").over(window_spec)
).withColumn(
    "amount_variance", F.col("amount_std") / (F.col("avg_amount") + 1)
)

# Categorical encoding
df_features = df_features.withColumn(
    "category_encoded",
    F.when(F.col("category") == "A", 1)
    .when(F.col("category") == "B", 2)
    .otherwise(0),
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Feature Selection

# COMMAND ----------

feature_columns = [
    "customer_id",
    "source_timestamp",
    "days_since_last_event",
    "event_count",
    "avg_amount",
    "total_amount",
    "max_amount",
    "min_amount",
    "amount_std",
    "amount_variance",
    "category_encoded",
    "target",
]

df_final = df_features.select(feature_columns)

# Remove nulls
df_final = df_final.na.drop()

final_row_count = df_final.count()
print(
    f"Final features: {final_row_count:,} rows, {len(feature_columns)} columns"
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Save Features

# COMMAND ----------

if spark.catalog.tableExists(features_table):
    delta_features = DeltaTable.forName(spark, features_table)
    delta_features.alias("t").merge(
        df_final.alias("s"),
        "t.customer_id = s.customer_id AND t.source_timestamp = s.source_timestamp",
    ).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
else:
    df_final.write.format("delta").mode("overwrite").saveAsTable(
        features_table
    )

# Optimize feature table for common lookup and join patterns.
spark.sql(
    f"OPTIMIZE {features_table} ZORDER BY (customer_id, source_timestamp)"
)

print(f"Features saved to: {features_table}")

# COMMAND ----------

result = {
    "status": "SUCCESS",
    "features_table": features_table,
    "feature_count": len(feature_columns),
    "row_count": final_row_count,
    "mode": "incremental" if latest_feature_ts is not None else "full",
    "quality_gates": {
        "null_ratio": null_ratio,
        "invalid_amount_count": invalid_amount_count,
        "invalid_category_count": invalid_category_count,
    },
    "storage_optimization": {"zorder_by": ["customer_id", "source_timestamp"]},
}

dbutils.notebook.exit(json.dumps(result))
