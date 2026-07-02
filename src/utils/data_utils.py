"""Data processing utilities for Spark DataFrames."""

from pyspark.sql import DataFrame
from typing import Any, Dict, List, Optional
import pyspark.sql.functions as F


def remove_duplicates(df: DataFrame, subset: Optional[List[str]] = None) -> DataFrame:
    """Remove duplicate rows from DataFrame.
    
    Args:
        df: Input Spark DataFrame
        subset: List of column names to consider for duplicates. If None, all columns used.
        
    Returns:
        DataFrame with duplicates removed
    """
    # Spark can skip a wider shuffle when we provide a subset explicitly.
    return df.dropDuplicates(subset=subset)


def handle_missing_values(
    df: DataFrame,
    strategy: str = "drop",
    subset: Optional[List[str]] = None,
    fill_value: Any = 0,
) -> DataFrame:
    """Handle missing values in DataFrame.
    
    Args:
        df: Input Spark DataFrame
        strategy: Strategy to use.
            - 'drop': remove rows with nulls
            - 'fill_zero': fill nulls with 0
            - 'fill': fill nulls with provided fill_value
        subset: Optional list of columns to scope null handling
        fill_value: Value (or dict of column -> value) used by 'fill' strategy
        
    Returns:
        DataFrame with missing values handled
        
    Raises:
        ValueError: If strategy is not recognized
    """
    strategies = {
        "drop": lambda d: d.na.drop(subset=subset),
        "fill_zero": lambda d: d.na.fill(0, subset=subset),
        "fill": lambda d: d.na.fill(fill_value, subset=subset)
        if not isinstance(fill_value, dict)
        else d.na.fill(fill_value),
    }
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


def summarize_missing_values(df: DataFrame) -> Dict[str, int]:
    """Return null counts by column in a single Spark pass.

    Args:
        df: Input Spark DataFrame

    Returns:
        Mapping of column name to null count for columns with nulls
    """
    if not df.columns:
        return {}

    counts_row = df.select([
        F.sum(F.col(column).isNull().cast("int")).alias(column) for column in df.columns
    ]).collect()[0]
    return {column: int(counts_row[column]) for column in df.columns if counts_row[column]}
