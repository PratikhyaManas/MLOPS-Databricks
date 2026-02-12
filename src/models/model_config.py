"""Model configuration loader"""

import yaml
import os
from typing import Dict, Any


def load_config(config_path: str = None) -> Dict[str, Any]:
    """Load model configuration from YAML file.
    
    Args:
        config_path: Path to config file. Defaults to config/model_config.yaml
        
    Returns:
        Dictionary containing model configuration
    """
    if config_path is None:
        # Resolve relative to this file's location
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "../../config/model_config.yaml")
    
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


# Load configuration at module level
_config = load_config()

# Export configuration with backward compatibility
RF_CONFIG = _config.get("models", {}).get("random_forest", {})
GB_CONFIG = _config.get("models", {}).get("gradient_boosting", {})
XGB_CONFIG = _config.get("models", {}).get("xgboost", {})
TRAINING_CONFIG = _config.get("training", {})
MLFLOW_CONFIG = _config.get("mlflow", {})
