"""Machine learning utilities"""

import mlflow
from typing import Dict, Iterable, Optional
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


def log_metrics(y_true: Iterable, y_pred: Iterable, prefix: str = "") -> Dict[str, float]:
    """Calculate and log common classification metrics.

    Uses zero_division=0 to prevent runtime failures on sparse class predictions.
    """
    metrics = {
        f"{prefix}accuracy": accuracy_score(y_true, y_pred),
        f"{prefix}precision": precision_score(y_true, y_pred, average='weighted', zero_division=0),
        f"{prefix}recall": recall_score(y_true, y_pred, average='weighted', zero_division=0),
        f"{prefix}f1_score": f1_score(y_true, y_pred, average='weighted', zero_division=0)
    }

    mlflow.log_metrics(metrics)
    return metrics


def get_best_run(experiment_name: str, metric: str = "f1_score") -> Optional[object]:
    """Get best run from experiment by metric"""
    client = mlflow.tracking.MlflowClient()
    experiment = mlflow.get_experiment_by_name(experiment_name)
    if not experiment:
        raise ValueError(f"Experiment '{experiment_name}' not found")
    
    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=[f"metrics.{metric} DESC"],
        max_results=1
    )
    
    return runs[0] if runs else None
