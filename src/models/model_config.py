"""Model configuration"""

# Random Forest configuration
RF_CONFIG = {
    "n_estimators": 100,
    "max_depth": 10,
    "min_samples_split": 5,
    "random_state": 42
}

# Gradient Boosting configuration
GB_CONFIG = {
    "n_estimators": 100,
    "learning_rate": 0.1,
    "max_depth": 5,
    "random_state": 42
}

# XGBoost configuration
XGB_CONFIG = {
    "n_estimators": 100,
    "max_depth": 6,
    "learning_rate": 0.1,
    "random_state": 42
}
