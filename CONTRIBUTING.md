# Contributing Guidelines

This document provides guidelines for contributing to the MLOps-Databricks repository.

## Code Style and Standards

### Python Code

#### Imports
- Use **explicit imports**, never use wildcard imports (`from module import *`)
- Group imports in this order: stdlib, third-party, local
- Example:
  ```python
  import os
  from typing import Dict, List
  
  import pyspark.sql.functions as F
  from pyspark.sql import DataFrame
  
  from src.utils.data_utils import remove_duplicates
  ```

#### Type Hints
- Always add type hints to function parameters and return values
- Use `Optional` for nullable types, `Union` for multiple types
- Example:
  ```python
  def process_data(df: DataFrame, subset: Optional[List[str]] = None) -> DataFrame:
      """Process data with optional column filtering"""
      ...
  ```

#### Docstrings
- Use the structured format with sections: Description, Args, Returns, Raises
- Example:
  ```python
  def remove_duplicates(df: DataFrame, subset: Optional[List[str]] = None) -> DataFrame:
      \"\"\"Remove duplicate rows from DataFrame.
      
      Args:
          df: Input Spark DataFrame
          subset: List of column names to consider for duplicates. If None, all columns used.
          
      Returns:
          DataFrame with duplicates removed
          
      Raises:
          ValueError: If subset contains invalid column names
      \"\"\"
      ...
  ```

#### Module Exports
- Always define `__all__` in module `__init__.py` files
- Export only public APIs
- Example:
  ```python
  # src/utils/__init__.py
  from .data_utils import remove_duplicates, handle_missing_values
  from .ml_utils import log_metrics
  
  __all__ = [
      "remove_duplicates",
      "handle_missing_values",
      "log_metrics",
  ]
  ```

### Code Quality Tools

#### Linting (Flake8)
- Run before committing: `flake8 src/ tests/`
- Configuration: Max line length 100, ignore E203, W503

#### Formatting (Black)
- Auto-format code: `black src/ tests/`
- Always check before commit: `black --check src/ tests/`

#### Type Checking (MyPy)
- Validate types: `mypy src/ --ignore-missing-imports`
- Add type hints to all public functions

---

## Testing Guidelines

### Test Organization
- Organize tests into classes by function being tested
- Use descriptive test names: `test_<function>_<scenario>`
- Example:
  ```python
  class TestRemoveDuplicates:
      @pytest.mark.unit
      def test_remove_duplicates_basic(self, spark):
          """Test basic duplicate removal"""
          ...
  ```

### Test Markers
- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - Tests requiring external resources
- `@pytest.mark.slow` - Long-running tests

### Running Tests
```bash
# Run all unit tests
pytest tests/ -v -m unit

# Run with coverage
pytest tests/ -v --cov=src --cov-report=html

# Run specific test class
pytest tests/test_data_utils.py::TestRemoveDuplicates -v
```

### Coverage Requirements
- Minimum coverage: 70%
- Aim for: 80%+
- Critical path: 95%+

---

## Configuration Management

### Strategy
The project uses **centralized configuration** via YAML to eliminate duplication and provide a single source of truth.

```
config/model_config.yaml
      ↓ (load_config())
Python constants (RF_CONFIG, GB_CONFIG, etc.)
```

### Configuration Files

**`config/model_config.yaml`** - All model and training configurations:
```yaml
models:
  random_forest:
    n_estimators: 100
    max_depth: 10
  xgboost:
    n_estimators: 100
    objective: 'binary:logistic'

training:
  test_size: 0.2
  validation_size: 0.1
  stratify: true
```

### Usage Pattern

**Option 1:** Load full config
```python
from src.models import load_config
config = load_config()
rf_params = config["models"]["random_forest"]
```

**Option 2:** Use exported constants (backward compatible)
```python
from src.models import RF_CONFIG, TRAINING_CONFIG
model = RandomForestClassifier(**RF_CONFIG)
```

**Option 3:** Custom config path
```python
config = load_config("/path/to/custom/config.yaml")
```

### Best Practices
1. **Use YAML for configuration** (not hardcoded dicts)
2. **Load dynamically** via `load_config()`
3. **Keep in `config/` directory**
4. **Never commit secrets** - use environment variables

---

## Dependency Management

### Adding Dependencies
1. Add to `requirements.txt` with version constraints
2. Run `pip install -r requirements.txt`
3. Test thoroughly
4. Update `setup.py` if needed (it reads from requirements.txt)

### Version Constraints
- Use minimum versions: `package>=1.0.0`
- Avoid overly restrictive: Not `package==1.0.0` (use this only for known issues)
- Example: `mlflow>=2.10.0, scikit-learn>=1.3.2`

### Strategy
```
mlfPerformance Checklist

- [ ] Data partitioned appropriately by common filters
- [ ] Spark cluster configured for auto-scaling
- [ ] No single-point bottlenecks in pipeline
- [ ] Logs don't grow unbounded
- [ ] Cache invalidation handled properly
- [ ] Error handling and retries in place
- [ ] Monitoring and alerts configured

---

## low>=2.10.0          # Allow patch updates
scikit-learn>=1.3.0,<2  # Allow minor updates, pin major
pyspark==3.5.0          # Pin exact for Databricks compatibility
```

### Update Safety
1. Always create a branch for dependency updates
2. Run full test suite before merging
3. Verify no breaking changes

---

## Git Workflow

### Branch Naming
- Feature: `feature/short-description`
- Bug fix: `bugfix/short-description`
- Hotfix: `hotfix/short-description`

### Commit Messages
- Use present tense: "Add feature" not "Added feature"
- Be descriptive but concise
- Example: `Add comprehensive type hints to data_utils module`

### Before Pushing
1. Run linting: `flake8 src/ tests/`
2. Run formatter: `black src/ tests/`
3. Run tests: `pytest tests/ -v`
4. Run type checker: `mypy src/ --ignore-missing-imports`

### Notebook Logging
Use logging utilities for tracking notebook execution:

```python
from src.notebooks.notebook_utils import log_notebook_run

log_notebook_run("03_model_training", status="started")
try:
    # Training code
    log_notebook_run("03_model_training", status="completed", 
                     message="Trained 3 models, best: RF with 0.92 AUC")
except Exception as e:
    log_notebook_run("03_model_training", status="failed", message=str(e))
    raise
```

### Best Practices
- Log all hyperparameters to MLflow
- Track data lineage with metadata columns
- Monitor training/inference time
- Alert on performance degradation

---

## Security Best Practices

### Secrets Management
**Good:**
```python
from os import getenv

databricks_token = getenv("DATABRICKS_TOKEN")
if not databricks_token:
    raise ValueError("DATABRICKS_TOKEN not set")
```

**Bad:**
```python
databricks_token = "dapi-abc123..."  # Never hardcode!
```

### In Azure Pipelines
```yaml
- script: deploy.sh
  env:
    DATABRICKS_TOKEN: $(DATABRICKS_TOKEN)  # From secret variable
```

### Configuration Files
- Never commit `*.env` files
- Add to `.gitignore`:
  ```
  .env
  .env.local
  secrets/
  .databricks.cfg
  ```

---

## Spark/Delta Optimization Patterns

### Table Creation (Optimized)
```python
# Before: Basic write
df.write.format("delta").mode("overwrite").saveAsTable("table")

# After: Optimized with partitioning
df.write \
    .format("delta") \
    .mode("overwrite") \
    .partitionBy("date") \
    .option("mergeSchema", "true") \
    .bucketBy(10, "customer_id") \
    .saveAsTable("table")
```

**Benefits:** Faster queries, better schema evolution, optimized for common filters

### Data Quality Checks
```python
from src.notebooks.notebook_utils import (
    validate_required_columns,
    get_null_counts,
    profile_dataframe
)

# Quick validation
validate_required_columns(df, ["id", "timestamp"])
nulls = get_null_counts(df)
profile = profile_dataframe(df)
```

### Memory Optimization
**Stream large data:**
```python
for partition in df.repartition(100).toLocalIterator():
    process_partition(partition)
```

**Data types matter:**
```python
df = df \
    .withColumn("age", F.col("age").cast("int")) \      # Not long
    .withColumn("score", F.col("score").cast("float"))   # Not double
```

**Result:** 40-50% memory reduction

### Partitioning Strategy
```python
# Good: Partition by commonly filtered columns
.partitionBy("year", "month", "customer_segment")

# Avoid: Too many partitions
.partitionBy("customer_id")  # Creates 1000s of small files
```

---

## Debugging & Profiling

### Logging Levels
```python
import logging

logger = logging.getLogger(__name__)
logger.debug("Detailed execution info")      # Not in production
logger.info("Important business events")     # Default level
logger.warning("Deprecated features")        # Warnings
logger.error("Error conditions")             # Critical issues
```

### Performance Profiling
```python
import time

start = time.time()
result = expensive_operation()
elapsed = time.time() - start
print(f"Completed in {elapsed:.2f}s")
```

---

## Notebook Development

### Use Shared Utilities
Always use utilities from `notebook_utils` in notebooks:

```python
from src.notebooks.notebook_utils import (
    validate_required_columns,
    get_null_counts,
    create_delta_table,
    add_processing_metadata
)

# Validate data structure
validate_required_columns(df, ["id", "timestamp", "feature1"])

# Profile data quality
null_counts = get_null_counts(df)
print(f"Null counts: {null_counts}")

# Create Delta table
create_delta_table(df, catalog="main", schema="mlops", table_name="features")

# Add metadata
df = add_processing_metadata(df, source="raw_data", stage="engineering")
```

### Logging
Use the logging utilities for tracking:
```python
from src.notebooks.notebook_utils import log_notebook_run

log_notebook_run("03_model_training", status="started")
# ... training code ...
log_notebook_run("03_model_training", status="completed", message="Successfully trained XGBoost model")
```

---

## CI/CD Pipeline

### Automatic Checks
The Azure Pipeline runs automatically on:
- Pull requests to main/develop branches
- Commits to main/develop branches

### Pipeline Stages
1. **Test**: Linting, type checking, unit tests, coverage
2. **Build**: Create Python wheel package
3. **Deploy**: Push to Dev (develop), Staging, Prod (main)

### Local Testing
Before pushing, test locally:
```bash
# Full test suite
python -m pytest tests/ -v --cov=src

# Only unit tests
python -m pytest tests/ -v -m unit

# With coverage report
python -m pytest tests/ --cov=src --cov-report=html
```

---

## Performance Optimization

### Spark/Delta Best Practices
1. **Partition data** for large tables by date
2. **Use Delta format** for ACID transactions
3. **Optimize cluster configuration** in deployment
4. **Cache DataFrames** when reused multiple times

### Example
```python
# Good: Partitioned write
df.write \
    .format("delta") \
    .mode("overwrite") \
    .partitionBy("date") \
    .saveAsTable("catalog.schema.table")

# Avoid: Unoptimized read
for row in df.collect():  # Too slow for large data
    process(row)

# Better: Vectorized operations
from pyspark.sql import functions as F
df.filter(F.col("value") > threshold)
```

---

## Code Review Checklist

Before reviewing, ensure:
- [ ] Code follows style guidelines
- [ ] Type hints are present
- [ ] Docstrings are complete
- [ ] No wildcard imports
- [ ] Tests are added for new code
- [ ] No hardcoded values/secrets
- [ ] Configuration is externalized
- [ ] Performance is acceptable

---

## Contact and Questions

For questions about these guidelines, please:
1. Check existing issues/discussions
2. Review the `OPTIMIZATION.md` for what changed
3. Check code docstrings for function usage

---

*Last updated: February 12, 2026*

*Last updated: February 12, 2026*
