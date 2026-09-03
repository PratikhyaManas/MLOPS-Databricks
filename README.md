# Databricks Asset Bundle - MLOps Production Pipeline

Complete MLOps pipeline using Databricks Asset Bundles for production-ready machine learning workflows.

## 🎯 Overview

This project implements an end-to-end MLOps pipeline on Databricks using Asset Bundles, featuring:

- **Automated ML Workflows**: Complete training, validation, and deployment pipelines
- **MLflow Integration**: Experiment tracking, model registry, and versioning
- **Multi-Environment Support**: Dev, Staging, and Production environments
- **CI/CD Automation**: GitHub Actions for automated testing and deployment
- **Unity Catalog**: Centralized data governance and management
- **Model Serving**: Real-time inference endpoints

## 📁 Project Structure

```
databricks_mlops_bundle/
├── databricks.yml              # Main bundle configuration
├── src/
│   ├── notebooks/              # Databricks notebooks
│   │   ├── 01_data_ingestion.py
│   │   ├── 02_feature_engineering.py
│   │   ├── 03_model_training.py
│   │   ├── 04_model_validation.py
│   │   ├── 05_model_registration.py
│   │   └── 06_batch_inference.py
│   ├── utils/                  # Utility functions
│   │   ├── data_utils.py
│   │   └── ml_utils.py
│   └── models/                 # Model configurations
│       └── model_config.py
├── tests/                      # Unit tests
│   ├── test_data_utils.py
│   └── test_ml_utils.py
├── config/                     # Configuration files
│   ├── model_config.yaml
│   └── cluster_config.json
├── deployment/                 # Deployment scripts
│   ├── deploy.sh
│   └── rollback.sh
├── .github/workflows/          # CI/CD workflows
│   └── ci-cd.yml
├── pyproject.toml             # Python dependencies and tool configuration
```

## 🚀 Quick Start

### Prerequisites

- Databricks workspace (AWS, Azure, or GCP)
- Databricks CLI installed
- Python 3.10+
- Unity Catalog enabled

### 1. Setup Databricks CLI

```bash
# Install Databricks CLI
curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh

# Configure authentication
databricks configure --token
```

### 2. Clone and Setup

```bash
git clone <repository-url>
cd databricks_mlops_bundle

# Create the project environment and install dependencies
uv sync --extra dev

# Activate the environment for local commands
# On PowerShell: .venv\Scripts\Activate.ps1
# On bash/zsh: source .venv/bin/activate
```

### 3. Validate Bundle

```bash
# Validate for development
databricks bundle validate -t dev

# Validate for production
databricks bundle validate -t prod
```

### 4. Deploy

```bash
# Deploy to development
databricks bundle deploy -t dev

# Deploy to production
databricks bundle deploy -t prod
```

### 5. Run Pipeline

```bash
# Run training pipeline
databricks bundle run ml_training_pipeline -t dev

# Run batch inference
databricks bundle run batch_inference_pipeline -t dev
```

## 📊 Pipeline Workflows

### Training Pipeline

The ML training pipeline consists of 5 stages:

1. **Data Ingestion** (`01_data_ingestion.py`)
   - Loads raw data from source
   - Performs data quality checks
   - Writes to Delta Lake

2. **Feature Engineering** (`02_feature_engineering.py`)
   - Creates ML features
   - Handles missing values
   - Saves feature table

3. **Model Training** (`03_model_training.py`)
   - Trains multiple models (Random Forest, Gradient Boosting)
   - Tracks experiments in MLflow
   - Selects best model

4. **Model Validation** (`04_model_validation.py`)
   - Validates model performance
   - Checks against thresholds
   - Ensures model quality

5. **Model Registration** (`05_model_registration.py`)
   - Registers model to MLflow Model Registry
   - Transitions to Staging/Production
   - Updates model metadata

### Inference Pipeline

6. **Batch Inference** (`06_batch_inference.py`)
   - Loads production model
   - Performs batch scoring
   - Saves predictions

## 🔧 Configuration

### Environment Variables

Create `.env` file:

```bash
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your-token-here
CATALOG_NAME=main
SCHEMA_NAME=mlops_prod
```

### Bundle Configuration

The `databricks.yml` file defines:

- **Jobs**: Training and inference pipelines
- **Clusters**: Compute resources
- **Experiments**: MLflow experiment tracking
- **Endpoints**: Model serving endpoints
- **Targets**: Dev, staging, prod environments

### Model Configuration

Edit `config/model_config.yaml`:

```yaml
models:
  random_forest:
    n_estimators: 100
    max_depth: 10

training:
  test_size: 0.2
  random_state: 42
```

## 🧪 Testing

```bash
# Run all tests with the project config
uv run pytest

# Run with coverage explicitly
uv run pytest --cov=src --cov-report=term-missing:skip-covered --cov-report=html

# Run a single test file
uv run pytest tests/test_data_utils.py
```

## 🔄 CI/CD

GitHub Actions workflow automatically:

1. **On Pull Request**: Runs tests and linting
2. **On Merge to Develop**: Deploys to dev environment
3. **On Merge to Main**: Deploys to production (with approval)

### Manual Deployment

```bash
# Using deployment script
./deployment/deploy.sh dev

# With job execution
./deployment/deploy.sh prod --run-job
```

## 📈 Monitoring and Logging

- **MLflow**: Track experiments, models, and metrics
- **Databricks Jobs**: Monitor job runs and logs
- **Delta Lake**: Audit data changes
- **Model Registry**: Track model versions and stages

## 🏗️ Architecture

```
┌─────────────────┐
│   Data Source   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Data Ingestion  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Feature Engineer │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Model Training  │
│    (MLflow)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Model Validation │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Model Registry   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Model Serving   │
│  (Endpoints)    │
└─────────────────┘
```

## 🔐 Security

- Use Databricks secrets for sensitive data
- Implement RBAC with Unity Catalog
- Use service principals for production
- Enable audit logging

## 📝 Best Practices

1. **Version Control**: All code in Git
2. **Testing**: Unit tests for all utilities
3. **Validation**: Model validation before deployment
4. **Monitoring**: Track model performance
5. **Documentation**: Keep docs updated
6. **Reproducibility**: Pin dependencies

## 🐛 Troubleshooting

### Bundle Validation Fails

```bash
# Check bundle syntax
databricks bundle validate -t dev

# Check workspace permissions
databricks workspace ls /
```

### Job Fails

```bash
# View job logs
databricks jobs list
databricks jobs get-run <run-id>
```

### Model Registration Issues

```bash
# Check MLflow experiments
databricks experiments list
```

## 🤝 Contributing

1. Create feature branch
2. Make changes
3. Add tests
4. Submit pull request

## 📚 Resources

- [Databricks Asset Bundles](https://docs.databricks.com/dev-tools/bundles/)
- [MLflow Documentation](https://mlflow.org/docs/latest/)
- [Unity Catalog](https://docs.databricks.com/data-governance/unity-catalog/)
- [Delta Lake](https://docs.delta.io/)
