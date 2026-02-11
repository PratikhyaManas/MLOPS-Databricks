"""Data processing utilities"""

from pyspark.sql import DataFrame
import pyspark.sql.functions as F


def remove_duplicates(df: DataFrame, subset=None) -> DataFrame:
    """Remove duplicate rows"""
    return df.dropDuplicates(subset=subset)


def handle_missing_values(df: DataFrame, strategy="drop") -> DataFrame:
    """Handle missing values"""
    if strategy == "drop":
        return df.na.drop()
    elif strategy == "fill_zero":
        return df.na.fill(0)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")


def add_audit_columns(df: DataFrame) -> DataFrame:
    """Add audit columns for tracking"""
    return df \
        .withColumn("created_at", F.current_timestamp()) \
        .withColumn("created_by", F.lit("ml_pipeline"))
