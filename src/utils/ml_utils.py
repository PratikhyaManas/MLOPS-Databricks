"""Machine learning utilities"""

import mlflow
from typing import Dict, Tuple
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


def log_metrics(y_true: list, y_pred: list, prefix: str = "") -> Dict[str, float]:
    """Calculate and log ML metrics"""
    metrics = {
        f"{prefix}accuracy": accuracy_score(y_true, y_pred),
        f"{prefix}precision": precision_score(y_true, y_pred, average='weighted'),
        f"{prefix}recall": recall_score(y_true, y_pred, average='weighted'),
        f"{prefix}f1_score": f1_score(y_true, y_pred, average='weighted')
    }
    
    mlflow.log_metrics(metrics)
    return metrics


def get_best_run(experiment_name: str, metric: str = "f1_score") -> Tuple[any, None]:
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
