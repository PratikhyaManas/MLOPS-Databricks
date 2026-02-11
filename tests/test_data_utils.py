"""Tests for data utilities"""

import pytest
from pyspark.sql import SparkSession
from src.utils.data_utils import *


@pytest.fixture(scope="session")
def spark():
    return SparkSession.builder \
        .appName("test") \
        .master("local[*]") \
        .getOrCreate()


def test_remove_duplicates(spark):
    data = [(1, "a"), (1, "a"), (2, "b")]
    df = spark.createDataFrame(data, ["id", "value"])
    
    result = remove_duplicates(df)
    assert result.count() == 2


def test_handle_missing_values(spark):
    data = [(1, None), (2, "b")]
    df = spark.createDataFrame(data, ["id", "value"])
    
    result = handle_missing_values(df, strategy="drop")
    assert result.count() == 1
