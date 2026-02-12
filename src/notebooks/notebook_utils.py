"""Common utilities for Databricks notebooks"""

from pyspark.sql import DataFrame, SparkSession
from typing import List, Dict, Any
import pyspark.sql.functions as F
from datetime import datetime


def get_spark_session() -> SparkSession:
    """Get or create Spark session (simplified for notebooks)"""
    return SparkSession.getActiveSession()


def log_notebook_run(notebook_name: str, status: str = "started", message: str = "") -> None:
    """Log notebook execution for tracking and debugging
    
    Args:
        notebook_name: Name of the notebook being executed
        status: Status of execution (started, completed, failed)
        message: Additional message or error details
    """
    spark = get_spark_session()
    log_entry = {
        "notebook": notebook_name,
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "message": message
    }
    print(f"[{status.upper()}] {notebook_name}: {message}")


def validate_required_columns(df: DataFrame, required_cols: List[str]) -> bool:
    """Validate that required columns exist in DataFrame
    
    Args:
        df: Spark DataFrame to validate
        required_cols: List of required column names
        
    Returns:
        True if all columns present, raises ValueError otherwise
    """
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return True


def get_null_counts(df: DataFrame) -> Dict[str, int]:
    """Get null counts for all columns
    
    Args:
        df: Spark DataFrame
        
    Returns:
        Dictionary mapping column names to null counts
    """
    null_counts = {}
    for col in df.columns:
        count = df.filter(F.col(col).isNull()).count()
        if count > 0:
            null_counts[col] = count
    return null_counts


def create_delta_table(df: DataFrame, catalog: str, schema: str, table_name: str, 
                      mode: str = "overwrite", merge_keys: List[str] = None) -> None:
    """Write DataFrame to Delta table with optimized settings
    
    Args:
        df: Spark DataFrame to write
        catalog: Catalog name
        schema: Schema name
        table_name: Table name
        mode: Write mode (overwrite, append, etc.)
        merge_keys: Columns for merge (if using merge approach)
    """
    full_table_name = f"{catalog}.{schema}.{table_name}"
    
    df.write \
        .format("delta") \
        .mode(mode) \
        .option("mergeSchema", "true") \
        .saveAsTable(full_table_name)
    
    print(f"Successfully created/updated table: {full_table_name}")


def add_processing_metadata(df: DataFrame, source: str, stage: str) -> DataFrame:
    """Add metadata columns for data lineage tracking
    
    Args:
        df: Spark DataFrame
        source: Data source identifier
        stage: Processing stage identifier
        
    Returns:
        DataFrame with added metadata columns
    """
    return df \
        .withColumn("data_source", F.lit(source)) \
        .withColumn("processing_stage", F.lit(stage)) \
        .withColumn("processed_at", F.current_timestamp())


def profile_dataframe(df: DataFrame) -> Dict[str, Any]:
    """Generate a profile of the DataFrame
    
    Args:
        df: Spark DataFrame to profile
        
    Returns:
        Dictionary with profile information
    """
    return {
        "row_count": df.count(),
        "column_count": len(df.columns),
        "columns": df.columns,
        "null_counts": get_null_counts(df),
        "memory_size": str(df.memory_usage(deep=True).sum()) if hasattr(df, 'memory_usage') else "N/A"
    }
