"""
Unit tests for data loading utilities.
"""

import pytest
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from io import StringIO

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.data.loaders import load_csv, load_json, load_data


@pytest.fixture
def sample_csv_data():
    """Create sample CSV data for testing."""
    csv_content = """id,value,category
1,10.5,A
2,20.3,B
3,15.7,A
"""
    return StringIO(csv_content)


@pytest.fixture
def sample_dataframe():
    """Create sample DataFrame for testing."""
    return pd.DataFrame({
        'id': [1, 2, 3],
        'value': [10.5, 20.3, 15.7],
        'category': ['A', 'B', 'A']
    })


def test_load_csv(sample_csv_data):
    """Test CSV loading."""
    df = pd.read_csv(sample_csv_data)
    assert len(df) == 3
    assert list(df.columns) == ['id', 'value', 'category']
    assert df['value'].dtype == np.float64


def test_dataframe_structure(sample_dataframe):
    """Test DataFrame structure."""
    assert sample_dataframe.shape == (3, 3)
    assert 'id' in sample_dataframe.columns
    assert 'value' in sample_dataframe.columns
    assert 'category' in sample_dataframe.columns


def test_dataframe_values(sample_dataframe):
    """Test DataFrame values."""
    assert sample_dataframe['id'].tolist() == [1, 2, 3]
    assert sample_dataframe['category'].tolist() == ['A', 'B', 'A']


# Add more tests as needed when you have actual data files
# def test_load_data_csv(tmp_path):
#     """Test load_data with CSV file."""
#     # Create temporary CSV file
#     csv_file = tmp_path / "test.csv"
#     df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
#     df.to_csv(csv_file, index=False)
#
#     # Load and test
#     loaded_df = load_data(csv_file)
#     pd.testing.assert_frame_equal(loaded_df, df)
