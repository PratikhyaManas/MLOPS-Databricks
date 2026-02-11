"""Tests for ML utilities"""

import pytest
from src.utils.ml_utils import log_metrics
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier


def test_log_metrics():
    X, y = make_classification(n_samples=100, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)
    
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    # This would normally log to MLflow
    # For testing, we just check it runs without error
    metrics = log_metrics(y_test, y_pred, prefix="test_")
    
    assert "test_accuracy" in metrics
    assert metrics["test_accuracy"] > 0
