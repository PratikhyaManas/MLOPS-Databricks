# MLOPS Databricks

A compact Databricks MLOps project for data processing, model training, validation, and batch inference. The repository is structured to run locally with `uv` and ships with unit tests and a Databricks Asset Bundle configuration for deployment.

## Overview

This project includes:

- Spark-based data utilities for cleaning and auditing data
- ML utilities for metric logging with MLflow
- YAML-backed model configuration loading
- Databricks notebook templates for ingestion, feature engineering, training, validation, registration, and batch inference
- A local testing setup using `pytest` and coverage

## Repository structure

```text
.
├── databricks.yml               # Databricks Asset Bundle config
├── pyproject.toml               # Project metadata and dependency config
├── README.md                    # Project documentation
├── config/
│   └── model_config.yaml        # Model and training defaults
├── deployment/
│   ├── deploy.sh
│   └── rollback.sh
├── src/
│   ├── models/
│   │   ├── __init__.py
│   │   └── model_config.py
│   ├── notebooks/
│   │   ├── 01_data_ingestion.py
│   │   ├── 02_feature_engineering.py
│   │   ├── 03_model_training.py
│   │   ├── 04_model_validation.py
│   │   ├── 05_model_registration.py
│   │   ├── 06_batch_inference.py
│   │   └── notebook_utils.py
│   └── utils/
│       ├── __init__.py
│       ├── data_utils.py
│       └── ml_utils.py
├── tests/
│   ├── test_data_utils.py
│   ├── test_ml_utils.py
│   └── test_model_config.py
├── .venv/                       # Created by uv
├── coverage.xml
├── htmlcov/
└── .gitignore
```

## Prerequisites

- `uv` installed
- Python 3.10+ (the project was verified with Python 3.12 in this environment)
- Java 11 for local PySpark execution on Windows
- Databricks CLI and workspace access for deployment targets

### Windows local Spark requirement

For local Spark runs on Windows, set:

```powershell
$env:JAVA_HOME = 'C:\Program Files\Java\jdk-11'
$env:PATH = 'C:\Program Files\Java\jdk-11\bin;' + $env:PATH
$env:PYSPARK_PYTHON = (Resolve-Path .\.venv\Scripts\python.exe).Path
$env:PYSPARK_DRIVER_PYTHON = $env:PYSPARK_PYTHON
```

This was required to make the local Spark dry run work correctly in this environment.

## Quick start

```bash
git clone <repo-url>
cd MLOPS-Databricks
uv sync --extra dev
```

Activate the virtual environment when needed:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Run tests

```powershell
$env:JAVA_HOME = 'C:\Program Files\Java\jdk-11'
$env:PATH = 'C:\Program Files\Java\jdk-11\bin;' + $env:PATH
$env:PYSPARK_PYTHON = (Resolve-Path .\.venv\Scripts\python.exe).Path
$env:PYSPARK_DRIVER_PYTHON = $env:PYSPARK_PYTHON
uv run pytest -q
```

Verified result in this repo: 15 tests passed with 83.33% coverage.

## Dry run check

This minimal Spark check verifies the local runtime is healthy:

```powershell
$env:JAVA_HOME = 'C:\Program Files\Java\jdk-11'
$env:PATH = 'C:\Program Files\Java\jdk-11\bin;' + $env:PATH
$env:PYSPARK_PYTHON = (Resolve-Path .\.venv\Scripts\python.exe).Path
$env:PYSPARK_DRIVER_PYTHON = $env:PYSPARK_PYTHON
uv run python -c "from pyspark.sql import SparkSession; s = SparkSession.builder.master('local[*]').appName('probe').getOrCreate(); print(s.version); print(s.createDataFrame([(1, None), (2, 'b')], ['id', 'value']).collect()); s.stop()"
```

## Databricks bundle usage

Validate and deploy the project bundle with Databricks CLI:

```bash
databricks bundle validate -t dev
databricks bundle deploy -t dev
```

Run jobs defined in the bundle:

```bash
databricks bundle run ml_training_pipeline -t dev
databricks bundle run batch_inference_pipeline -t dev
```

## Pipeline stages

1. Data ingestion
   - Reads raw data and validates required fields
2. Feature engineering
   - Creates derived features for training
3. Model training
   - Trains the configured model and logs metrics in MLflow
4. Model validation
   - Checks performance thresholds before promotion
5. Model registration
   - Registers the validated model in MLflow Model Registry
6. Batch inference
   - Scores new data in batch mode

## Configuration

The training and model settings are split across:

- [config/model_config.yaml](config/model_config.yaml)
- [src/models/model_config.py](src/models/model_config.py)

## Notes

- The project prefers `uv` as the package manager and environment manager.
- The repo was cleaned up to remove duplicated dependency/tooling metadata and now keeps a single source of truth in [pyproject.toml](pyproject.toml).
- Local Windows execution may require Java 11 and `PYSPARK_PYTHON`/`PYSPARK_DRIVER_PYTHON` to be set explicitly for PySpark worker processes.

## References

- [Databricks Asset Bundles](https://docs.databricks.com/dev-tools/bundles/)
- [MLflow](https://mlflow.org/docs/latest/)
- [Spark on Windows](https://spark.apache.org/)
- [Delta Lake](https://delta.io/)
