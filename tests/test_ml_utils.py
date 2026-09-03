"""Tests for ML utilities."""

import mlflow
import pytest
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from src.utils.ml_utils import log_metrics


class TestLogMetrics:
    """Tests for log_metrics function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup MLflow tracking."""
        mlflow.set_experiment("test-experiment")
        yield

    @pytest.mark.unit
    def test_log_metrics_returns_dict(self):
        """Test that log_metrics returns a dictionary."""
        X, y = make_classification(n_samples=100, random_state=42)
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            random_state=42,
        )

        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        with mlflow.start_run():
            metrics = log_metrics(y_test, y_pred, prefix="test_")

        assert isinstance(metrics, dict)
        assert "test_accuracy" in metrics
        assert "test_precision" in metrics
        assert "test_recall" in metrics
        assert "test_f1_score" in metrics

    @pytest.mark.unit
    def test_log_metrics_values_valid(self):
        """Test that metric values are reasonable."""
        X, y = make_classification(n_samples=100, random_state=42)
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            random_state=42,
        )

        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        with mlflow.start_run():
            metrics = log_metrics(y_test, y_pred)

        for value in metrics.values():
            assert 0 <= value <= 1, "Metrics should be between 0 and 1"

    @pytest.mark.unit
    def test_log_metrics_prefix_applied(self):
        """Test that prefix is correctly applied."""
        X, y = make_classification(n_samples=50, random_state=42)
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            random_state=42,
        )

        model = RandomForestClassifier(n_estimators=5, random_state=42)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        with mlflow.start_run():
            metrics = log_metrics(y_test, y_pred, prefix="custom_")

        assert all(k.startswith("custom_") for k in metrics)
