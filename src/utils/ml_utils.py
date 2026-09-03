"""Machine learning utilities."""

import mlflow
from numpy.typing import ArrayLike
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)


def log_metrics(
    y_true: ArrayLike,
    y_pred: ArrayLike,
    prefix: str = "",
) -> dict[str, float]:
    """Calculate and log common classification metrics.

    Uses zero_division=0 to prevent runtime failures on sparse class
    predictions.
    """
    metrics: dict[str, float] = {
        f"{prefix}accuracy": float(accuracy_score(y_true, y_pred)),
        f"{prefix}precision": float(
            precision_score(
                y_true,
                y_pred,
                average="weighted",
                zero_division=0,
            )
        ),
        f"{prefix}recall": float(
            recall_score(
                y_true,
                y_pred,
                average="weighted",
                zero_division=0,
            )
        ),
        f"{prefix}f1_score": float(
            f1_score(
                y_true,
                y_pred,
                average="weighted",
                zero_division=0,
            )
        ),
    }

    mlflow.log_metrics(metrics)
    return metrics


def get_best_run(
    experiment_name: str,
    metric: str = "f1_score",
) -> object | None:
    """Get best run from experiment by metric."""
    client = mlflow.MlflowClient()
    experiment = mlflow.get_experiment_by_name(experiment_name)
    if not experiment:
        raise ValueError(f"Experiment '{experiment_name}' not found")

    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=[f"metrics.{metric} DESC"],
        max_results=1,
    )

    return runs[0] if runs else None
