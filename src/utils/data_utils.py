"""Data processing utilities for Spark DataFrames"""

from pyspark.sql import DataFrame
from typing import Optional, List
import pyspark.sql.functions as F


def remove_duplicates(df: DataFrame, subset: Optional[List[str]] = None) -> DataFrame:
    """Remove duplicate rows from DataFrame.
    
    Args:
        df: Input Spark DataFrame
        subset: List of column names to consider for duplicates. If None, all columns used.
        
    Returns:
        DataFrame with duplicates removed
    """
    return df.dropDuplicates(subset=subset)


def handle_missing_values(df: DataFrame, strategy: str = "drop") -> DataFrame:
    """Handle missing values in DataFrame.
    
    Args:
        df: Input Spark DataFrame
        strategy: Strategy to use - 'drop' (remove rows with nulls) or 'fill_zero' (fill with 0)
        
    Returns:
        DataFrame with missing values handled
        
    Raises:
        ValueError: If strategy is not recognized
    """
    strategies = {"drop": lambda d: d.na.drop(), "fill_zero": lambda d: d.na.fill(0)}
    if strategy not in strategies:
        raise ValueError(f"Unknown strategy: {strategy}. Supported: {list(strategies.keys())}")
    return strategies[strategy](df)


def add_audit_columns(df: DataFrame, created_by: str = "ml_pipeline") -> DataFrame:
    """Add audit columns for tracking data lineage.
    
    Args:
        df: Input Spark DataFrame
        created_by: Name/identifier of pipeline creating the data
        
    Returns:
        DataFrame with audit columns (created_at, created_by)
    """
    return df.withColumn("created_at", F.current_timestamp()).withColumn("created_by", F.lit(created_by))
