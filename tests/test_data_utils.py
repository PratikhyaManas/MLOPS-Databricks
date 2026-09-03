"""Tests for data utilities"""

import pytest
from pyspark.sql import SparkSession
from src.utils.data_utils import remove_duplicates, handle_missing_values, add_audit_columns


@pytest.fixture(scope="session")
def spark():
    """Create a Spark session for testing"""
    return SparkSession.builder \
        .appName("test-data-utils") \
        .master("local[*]") \
        .getOrCreate()


class TestRemoveDuplicates:
    """Tests for remove_duplicates function"""
    
    @pytest.mark.unit
    def test_remove_duplicates_basic(self, spark):
        """Test basic duplicate removal"""
        data = [(1, "a"), (1, "a"), (2, "b")]
        df = spark.createDataFrame(data, ["id", "value"])
        
        result = remove_duplicates(df)
        assert result.count() == 2
    
    @pytest.mark.unit
    def test_remove_duplicates_no_duplicates(self, spark):
        """Test when there are no duplicates"""
        data = [(1, "a"), (2, "b"), (3, "c")]
        df = spark.createDataFrame(data, ["id", "value"])
        
        result = remove_duplicates(df)
        assert result.count() == 3
    
    @pytest.mark.unit
    def test_remove_duplicates_subset(self, spark):
        """Test duplicate removal with subset of columns"""
        data = [(1, "a"), (1, "b"), (2, "c")]
        df = spark.createDataFrame(data, ["id", "value"])
        
        result = remove_duplicates(df, subset=["id"])
        assert result.count() == 2


class TestHandleMissingValues:
    """Tests for handle_missing_values function"""
    
    @pytest.mark.unit
    def test_handle_missing_drop(self, spark):
        """Test dropping rows with missing values"""
        data = [(1, None), (2, "b")]
        df = spark.createDataFrame(data, ["id", "value"])
        
        result = handle_missing_values(df, strategy="drop")
        assert result.count() == 1
    
    @pytest.mark.unit
    def test_handle_missing_fill_zero(self, spark):
        """Test filling missing values with zero"""
        data = [(1, None), (2, 0)]
        df = spark.createDataFrame(data, ["id", "value"])
        
        result = handle_missing_values(df, strategy="fill_zero")
        assert result.count() == 2
    
    @pytest.mark.unit
    def test_handle_missing_invalid_strategy(self, spark):
        """Test invalid strategy raises error."""
        data = [(1, "a"), (2, "b")]
        schema = "id INT, value STRING"
        df = spark.createDataFrame(data, schema=schema)

        with pytest.raises(ValueError, match="Unknown strategy"):
            handle_missing_values(df, strategy="invalid")


class TestAddAuditColumns:
    """Tests for add_audit_columns function"""
    
    @pytest.mark.unit
    def test_add_audit_columns_default(self, spark):
        """Test adding audit columns with defaults"""
        data = [(1, "a")]
        df = spark.createDataFrame(data, ["id", "value"])
        
        result = add_audit_columns(df)
        expected_cols = ["id", "value", "created_at", "created_by"]
        assert sorted(result.columns) == sorted(expected_cols)
    
    @pytest.mark.unit
    def test_add_audit_columns_custom_user(self, spark):
        """Test adding audit columns with custom creator"""
        data = [(1, "a")]
        df = spark.createDataFrame(data, ["id", "value"])
        
        result = add_audit_columns(df, created_by="test_user")
        row = result.select("created_by").collect()[0]
        assert row.created_by == "test_user"
