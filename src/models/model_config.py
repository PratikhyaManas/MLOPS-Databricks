"""Model configuration loader."""

import os
from functools import lru_cache
from typing import Any, Dict, Optional

import yaml


def _default_config_path() -> str:
    """Resolve default configuration path relative to this module."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "../../config/model_config.yaml")


@lru_cache(maxsize=4)
def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load model configuration from YAML file.

    Args:
        config_path: Path to config file. Defaults to config/model_config.yaml

    Returns:
        Dictionary containing model configuration
    """
    if config_path is None:
        config_path = _default_config_path()

    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def _get_section(
    section: str, sub_section: Optional[str] = None
) -> Dict[str, Any]:
    config = load_config()
    if sub_section is None:
        return config.get(section, {})
    return config.get(section, {}).get(sub_section, {})


# Export configuration with backward compatibility.
RF_CONFIG = _get_section("models", "random_forest")
GB_CONFIG = _get_section("models", "gradient_boosting")
XGB_CONFIG = _get_section("models", "xgboost")
TRAINING_CONFIG = _get_section("training")
MLFLOW_CONFIG = _get_section("mlflow")
