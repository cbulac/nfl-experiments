"""
Data transformation utilities.
"""

from typing import List, Optional, Union
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder


def normalize_data(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    feature_range: tuple = (0, 1)
) -> pd.DataFrame:
    """
    Normalize numeric columns to a specified range.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame
    columns : list of str, optional
        Columns to normalize. If None, normalizes all numeric columns
    feature_range : tuple, default=(0, 1)
        Target range for normalized values

    Returns
    -------
    pd.DataFrame
        DataFrame with normalized columns
    """
    df_copy = df.copy()

    if columns is None:
        columns = df_copy.select_dtypes(include=[np.number]).columns.tolist()

    scaler = MinMaxScaler(feature_range=feature_range)
    df_copy[columns] = scaler.fit_transform(df_copy[columns])

    return df_copy


def standardize_data(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Standardize numeric columns (zero mean, unit variance).

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame
    columns : list of str, optional
        Columns to standardize. If None, standardizes all numeric columns

    Returns
    -------
    pd.DataFrame
        DataFrame with standardized columns
    """
    df_copy = df.copy()

    if columns is None:
        columns = df_copy.select_dtypes(include=[np.number]).columns.tolist()

    scaler = StandardScaler()
    df_copy[columns] = scaler.fit_transform(df_copy[columns])

    return df_copy


def encode_categorical(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    method: str = 'label'
) -> pd.DataFrame:
    """
    Encode categorical variables.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame
    columns : list of str, optional
        Columns to encode. If None, encodes all object/category columns
    method : str, default='label'
        Encoding method: 'label' or 'onehot'

    Returns
    -------
    pd.DataFrame
        DataFrame with encoded columns
    """
    df_copy = df.copy()

    if columns is None:
        columns = df_copy.select_dtypes(include=['object', 'category']).columns.tolist()

    if method == 'label':
        for col in columns:
            le = LabelEncoder()
            df_copy[col] = le.fit_transform(df_copy[col])
    elif method == 'onehot':
        df_copy = pd.get_dummies(df_copy, columns=columns)
    else:
        raise ValueError(f"Unknown encoding method: {method}")

    return df_copy


def remove_outliers(
    df: pd.DataFrame,
    columns: List[str],
    method: str = 'iqr',
    threshold: float = 1.5
) -> pd.DataFrame:
    """
    Remove outliers from specified columns.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame
    columns : list of str
        Columns to check for outliers
    method : str, default='iqr'
        Method for outlier detection: 'iqr' or 'zscore'
    threshold : float, default=1.5
        Threshold for outlier detection (IQR multiplier or z-score threshold)

    Returns
    -------
    pd.DataFrame
        DataFrame with outliers removed
    """
    df_copy = df.copy()

    for col in columns:
        if method == 'iqr':
            Q1 = df_copy[col].quantile(0.25)
            Q3 = df_copy[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            df_copy = df_copy[
                (df_copy[col] >= lower_bound) & (df_copy[col] <= upper_bound)
            ]
        elif method == 'zscore':
            z_scores = np.abs((df_copy[col] - df_copy[col].mean()) / df_copy[col].std())
            df_copy = df_copy[z_scores < threshold]
        else:
            raise ValueError(f"Unknown method: {method}")

    return df_copy
