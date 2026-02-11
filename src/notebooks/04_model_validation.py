# Databricks notebook source
# MAGIC %md
# MAGIC # Model Validation Pipeline
# MAGIC Validates model performance before deployment

# COMMAND ----------

import mlflow
from sklearn.metrics import *
import pandas as pd
import json

# COMMAND ----------

# Parameters
threshold = float(dbutils.widgets.get("threshold"))
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")

# COMMAND ----------

# MAGIC %md  
# MAGIC ## Load Best Model

# COMMAND ----------

# Get latest run
client = mlflow.tracking.MlflowClient()
experiment_path = dbutils.widgets.get("experiment_path")
experiment = mlflow.get_experiment_by_name(experiment_path)

runs = client.search_runs(
    experiment_ids=[experiment.experiment_id],
    order_by=["metrics.f1_score DESC"],
    max_results=1
)

best_run = runs[0]
model_uri = f"runs:/{best_run.info.run_id}/model"
model = mlflow.sklearn.load_model(model_uri)

print(f"Loaded model from run: {best_run.info.run_id}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load Validation Data

# COMMAND ----------

validation_table = f"{catalog}.{schema}.validation_data"
df_val = spark.table(validation_table).toPandas()

X_val = df_val.drop(columns=["customer_id", "target"])
y_val = df_val["target"]

# COMMAND ----------

# MAGIC %md
# MAGIC ## Validate Performance

# COMMAND ----------

y_pred = model.predict(X_val)
y_pred_proba = model.predict_proba(X_val)

# Metrics
val_metrics = {
    "val_accuracy": accuracy_score(y_val, y_pred),
    "val_f1_score": f1_score(y_val, y_pred, average='weighted'),
    "val_precision": precision_score(y_val, y_pred, average='weighted'),
    "val_recall": recall_score(y_val, y_pred, average='weighted')
}

print("Validation Metrics:")
for metric, value in val_metrics.items():
    print(f"  {metric}: {value:.4f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Performance Checks

# COMMAND ----------

# Check if meets threshold
validation_passed = val_metrics["val_f1_score"] >= threshold

if not validation_passed:
    raise ValueError(f"Model F1 score {val_metrics['val_f1_score']:.4f} below threshold {threshold}")

# Check for bias
from sklearn.metrics import confusion_matrix
cm = confusion_matrix(y_val, y_pred)

# Check class balance in predictions
class_distribution = pd.Series(y_pred).value_counts(normalize=True)
if (class_distribution < 0.05).any():
    print("WARNING: Some classes have very low prediction rates")

print("✓ All validation checks passed")

# COMMAND ----------

result = {
    "status": "SUCCESS",
    "validation_passed": validation_passed,
    "val_f1_score": val_metrics["val_f1_score"],
    "run_id": best_run.info.run_id
}

dbutils.notebook.exit(json.dumps(result))
