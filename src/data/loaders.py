"""
Data loading utilities for various file formats.
"""

from pathlib import Path
from typing import Optional, Union
import pandas as pd
import json


def load_csv(
    file_path: Union[str, Path],
    **kwargs
) -> pd.DataFrame:
    """
    Load data from a CSV file.

    Parameters
    ----------
    file_path : str or Path
        Path to the CSV file
    **kwargs
        Additional arguments to pass to pd.read_csv

    Returns
    -------
    pd.DataFrame
        Loaded data
    """
    return pd.read_csv(file_path, **kwargs)


def load_json(
    file_path: Union[str, Path],
    **kwargs
) -> Union[dict, pd.DataFrame]:
    """
    Load data from a JSON file.

    Parameters
    ----------
    file_path : str or Path
        Path to the JSON file
    **kwargs
        Additional arguments to pass to json.load or pd.read_json

    Returns
    -------
    dict or pd.DataFrame
        Loaded data
    """
    with open(file_path, 'r') as f:
        return json.load(f)


def load_data(
    file_path: Union[str, Path],
    file_type: Optional[str] = None,
    **kwargs
) -> pd.DataFrame:
    """
    Load data from various file formats.

    Parameters
    ----------
    file_path : str or Path
        Path to the data file
    file_type : str, optional
        Type of file ('csv', 'json', 'parquet'). If None, inferred from extension
    **kwargs
        Additional arguments to pass to the loading function

    Returns
    -------
    pd.DataFrame
        Loaded data

    Examples
    --------
    >>> data = load_data('data/raw/dataset.csv')
    >>> data = load_data('data/raw/dataset.json', file_type='json')
    """
    file_path = Path(file_path)

    if file_type is None:
        file_type = file_path.suffix.lstrip('.')

    loaders = {
        'csv': pd.read_csv,
        'json': pd.read_json,
        'parquet': pd.read_parquet,
        'xlsx': pd.read_excel,
        'xls': pd.read_excel
    }

    if file_type not in loaders:
        raise ValueError(f"Unsupported file type: {file_type}")

    return loaders[file_type](file_path, **kwargs)
