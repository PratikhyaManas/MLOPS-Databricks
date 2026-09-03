"""Tests for model configuration loading."""

from src.models.model_config import load_config, RF_CONFIG, TRAINING_CONFIG, MLFLOW_CONFIG


def test_load_config_returns_expected_sections():
    config = load_config()

    assert "models" in config
    assert "training" in config
    assert "mlflow" in config


def test_random_forest_defaults_loaded():
    assert RF_CONFIG["n_estimators"] == 100
    assert RF_CONFIG["max_depth"] == 10


def test_training_config_loaded():
    assert TRAINING_CONFIG["test_size"] == 0.2
    assert TRAINING_CONFIG["random_state"] == 42


def test_mlflow_config_loaded():
    assert MLFLOW_CONFIG["experiment_path"] == "/Shared/mlops-experiments"
