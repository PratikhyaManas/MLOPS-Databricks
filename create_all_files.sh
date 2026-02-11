#!/bin/bash

# Create all notebook files

cat > src/notebooks/01_data_ingestion.py << 'EOF'
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
EOF

cat > src/notebooks/02_feature_engineering.py << 'EOF'
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
EOF

cat > src/notebooks/03_model_training.py << 'EOF'
# Databricks notebook source
# MAGIC %md
# MAGIC # Model Training Pipeline
# MAGIC Trains ML models using MLflow

# COMMAND ----------

import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import *
import pandas as pd
import numpy as np

# COMMAND ----------

# Parameters
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
experiment_path = dbutils.widgets.get("experiment_path")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup MLflow

# COMMAND ----------

mlflow.set_experiment(experiment_path)
mlflow.sklearn.autolog(log_input_examples=True, log_model_signatures=True)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load Features

# COMMAND ----------

features_table = f"{catalog}.{schema}.ml_features"
df = spark.table(features_table).toPandas()

print(f"Loaded {len(df):,} rows for training")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prepare Data

# COMMAND ----------

# Separate features and target
X = df.drop(columns=["customer_id", "target"])
y = df["target"]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"Training set: {X_train.shape}")
print(f"Test set: {X_test.shape}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Train Random Forest

# COMMAND ----------

with mlflow.start_run(run_name="RandomForest") as run:
    # Model
    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1
    )
    
    # Train
    rf_model.fit(X_train, y_train)
    
    # Predictions  
    y_pred = rf_model.predict(X_test)
    y_pred_proba = rf_model.predict_proba(X_test)
    
    # Metrics
    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, average='weighted'),
        "recall": recall_score(y_test, y_pred, average='weighted'),
        "f1_score": f1_score(y_test, y_pred, average='weighted'),
        "roc_auc": roc_auc_score(y_test, y_pred_proba, multi_class='ovr')
    }
    
    # Log metrics
    mlflow.log_metrics(metrics)
    
    # Log model
    mlflow.sklearn.log_model(rf_model, "model", registered_model_name=None)
    
    rf_run_id = run.info.run_id
    
    print(f"Random Forest - F1: {metrics['f1_score']:.4f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Train Gradient Boosting

# COMMAND ----------

with mlflow.start_run(run_name="GradientBoosting") as run:
    gb_model = GradientBoostingClassifier(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        random_state=42
    )
    
    gb_model.fit(X_train, y_train)
    
    y_pred = gb_model.predict(X_test)
    y_pred_proba = gb_model.predict_proba(X_test)
    
    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, average='weighted'),
        "recall": recall_score(y_test, y_pred, average='weighted'),
        "f1_score": f1_score(y_test, y_pred, average='weighted'),
        "roc_auc": roc_auc_score(y_test, y_pred_proba, multi_class='ovr')
    }
    
    mlflow.log_metrics(metrics)
    mlflow.sklearn.log_model(gb_model, "model", registered_model_name=None)
    
    gb_run_id = run.info.run_id
    
    print(f"Gradient Boosting - F1: {metrics['f1_score']:.4f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Select Best Model

# COMMAND ----------

# Get best run
client = mlflow.tracking.MlflowClient()
experiment = mlflow.get_experiment_by_name(experiment_path)

runs = client.search_runs(
    experiment_ids=[experiment.experiment_id],
    order_by=["metrics.f1_score DESC"],
    max_results=1
)

best_run = runs[0]
best_model_uri = f"runs:/{best_run.info.run_id}/model"

print(f"Best Model Run ID: {best_run.info.run_id}")
print(f"Best F1 Score: {best_run.data.metrics['f1_score']:.4f}")

# COMMAND ----------

import json

result = {
    "status": "SUCCESS",
    "best_run_id": best_run.info.run_id,
    "best_f1_score": best_run.data.metrics['f1_score'],
    "model_uri": best_model_uri
}

dbutils.notebook.exit(json.dumps(result))
EOF

echo "✓ Created all notebook files"
