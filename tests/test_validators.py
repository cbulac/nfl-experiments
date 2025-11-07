"""
Unit tests for data validation utilities.
"""

import pytest
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.data.validators import (
    check_missing_values,
    validate_data,
    check_data_types
)


@pytest.fixture
def clean_dataframe():
    """Create a clean DataFrame with no issues."""
    return pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'value': [10.5, 20.3, 15.7, 18.2, 22.1],
        'category': ['A', 'B', 'A', 'C', 'B']
    })


@pytest.fixture
def messy_dataframe():
    """Create a DataFrame with missing values."""
    return pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'value': [10.5, np.nan, 15.7, np.nan, 22.1],
        'category': ['A', 'B', None, 'C', 'B']
    })


@pytest.fixture
def duplicate_dataframe():
    """Create a DataFrame with duplicate rows."""
    return pd.DataFrame({
        'id': [1, 2, 2, 3],
        'value': [10.5, 20.3, 20.3, 15.7],
        'category': ['A', 'B', 'B', 'A']
    })


def test_check_missing_values_clean(clean_dataframe):
    """Test missing value check on clean data."""
    missing = check_missing_values(clean_dataframe)
    assert len(missing) == 0


def test_check_missing_values_messy(messy_dataframe):
    """Test missing value check on messy data."""
    missing = check_missing_values(messy_dataframe)
    assert len(missing) > 0
    assert 'value' in missing.index
    assert 'category' in missing.index


def test_validate_data_clean(clean_dataframe):
    """Test validation on clean data."""
    results = validate_data(clean_dataframe)
    assert results['valid'] is True
    assert len(results['issues']) == 0


def test_validate_data_missing_values(messy_dataframe):
    """Test validation with missing values."""
    results = validate_data(messy_dataframe)
    assert len(results['issues']) > 0
    assert any('missing values' in issue.lower() for issue in results['issues'])


def test_validate_data_duplicates(duplicate_dataframe):
    """Test validation with duplicate rows."""
    results = validate_data(duplicate_dataframe)
    assert results['duplicate_count'] == 1
    assert any('duplicate' in issue.lower() for issue in results['issues'])


def test_validate_data_required_columns(clean_dataframe):
    """Test validation with required columns."""
    # Should pass with existing columns
    results = validate_data(clean_dataframe, required_columns=['id', 'value'])
    assert results['valid'] is True

    # Should fail with non-existing column
    results = validate_data(clean_dataframe, required_columns=['id', 'missing_col'])
    assert results['valid'] is False
    assert any('missing required columns' in issue.lower() for issue in results['issues'])


def test_check_data_types():
    """Test data type checking."""
    df = pd.DataFrame({
        'int_col': [1, 2, 3],
        'float_col': [1.0, 2.0, 3.0],
        'str_col': ['a', 'b', 'c']
    })

    expected_types = {
        'int_col': np.dtype('int64'),
        'float_col': np.dtype('float64'),
        'str_col': np.dtype('object')
    }

    results = check_data_types(df, expected_types)
    assert results['valid'] is True
    assert len(results['mismatches']) == 0


def test_check_data_types_mismatch():
    """Test data type checking with mismatches."""
    df = pd.DataFrame({
        'col1': [1, 2, 3],
        'col2': [1.0, 2.0, 3.0]
    })

    expected_types = {
        'col1': np.dtype('float64'),  # Wrong type
        'col2': np.dtype('float64')   # Correct type
    }

    results = check_data_types(df, expected_types)
    assert results['valid'] is False
    assert 'col1' in results['mismatches']
    assert 'col2' not in results['mismatches']


def test_missing_value_threshold():
    """Test missing value threshold parameter."""
    df = pd.DataFrame({
        'col1': [1, 2, np.nan, 4, 5],  # 20% missing
        'col2': [1, np.nan, np.nan, np.nan, 5]  # 60% missing
    })

    # With threshold of 0.5, only col2 should be reported
    missing = check_missing_values(df, threshold=0.5)
    assert len(missing) == 1
    assert 'col2' in missing.index

    # With threshold of 0.0, both should be reported
    missing = check_missing_values(df, threshold=0.0)
    assert len(missing) == 2
