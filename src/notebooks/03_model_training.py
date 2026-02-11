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
