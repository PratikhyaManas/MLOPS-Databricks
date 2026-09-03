# Databricks notebook source
# MAGIC %md
# MAGIC # Model Registration Pipeline
# MAGIC Registers validated model to MLflow Model Registry

# COMMAND ----------

import json

import mlflow
from mlflow.tracking import MlflowClient

# COMMAND ----------

# Parameters
model_name = dbutils.widgets.get("model_name")
experiment_path = dbutils.widgets.get("experiment_path")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Get Best Model

# COMMAND ----------

client = MlflowClient()
experiment = mlflow.get_experiment_by_name(experiment_path)

runs = client.search_runs(
    experiment_ids=[experiment.experiment_id],
    order_by=["metrics.f1_score DESC"],
    max_results=1,
)

best_run = runs[0]
run_id = best_run.info.run_id
model_uri = f"runs:/{run_id}/model"

print(f"Best model run ID: {run_id}")
print(f"F1 Score: {best_run.data.metrics['f1_score']:.4f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Register Model

# COMMAND ----------

# Register to MLflow Model Registry
model_details = mlflow.register_model(model_uri, model_name)

print(f"Model registered: {model_name}")
print(f"Version: {model_details.version}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Update Model Metadata

# COMMAND ----------

# Add description
client.update_model_version(
    name=model_name,
    version=model_details.version,
    description=(
        f"Model from run {run_id}. "
        f"F1 Score: {best_run.data.metrics['f1_score']:.4f}"
    ),
)

# Add tags
client.set_model_version_tag(
    name=model_name,
    version=model_details.version,
    key="validation_status",
    value="passed",
)

client.set_model_version_tag(
    name=model_name,
    version=model_details.version,
    key="f1_score",
    value=str(best_run.data.metrics["f1_score"]),
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Transition to Production

# COMMAND ----------

# Move to Staging first
client.transition_model_version_stage(
    name=model_name,
    version=model_details.version,
    stage="Staging",
    archive_existing_versions=False,
)

print(f"Model version {model_details.version} moved to Staging")

# After manual approval, transition to Production
# This would typically be done via a separate approval process
# client.transition_model_version_stage(
#     name=model_name,
#     version=model_details.version,
#     stage="Production",
#     archive_existing_versions=True
# )

# COMMAND ----------

result = {
    "status": "SUCCESS",
    "model_name": model_name,
    "model_version": model_details.version,
    "stage": "Staging",
    "run_id": run_id,
}

dbutils.notebook.exit(json.dumps(result))
