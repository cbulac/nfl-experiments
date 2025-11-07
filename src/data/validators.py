"""
Data validation utilities.
"""

from typing import List, Optional, Dict
import pandas as pd
import numpy as np


def check_missing_values(
    df: pd.DataFrame,
    threshold: float = 0.0
) -> pd.Series:
    """
    Check for missing values in a DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame
    threshold : float, default=0.0
        Proportion threshold above which to report columns (0.0 to 1.0)

    Returns
    -------
    pd.Series
        Proportion of missing values per column
    """
    missing = df.isnull().sum() / len(df)
    return missing[missing > threshold].sort_values(ascending=False)


def validate_data(
    df: pd.DataFrame,
    required_columns: Optional[List[str]] = None,
    check_duplicates: bool = True,
    check_missing: bool = True,
    missing_threshold: float = 0.0
) -> Dict[str, any]:
    """
    Validate DataFrame for common data quality issues.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame
    required_columns : list of str, optional
        Columns that must be present
    check_duplicates : bool, default=True
        Whether to check for duplicate rows
    check_missing : bool, default=True
        Whether to check for missing values
    missing_threshold : float, default=0.0
        Threshold for reporting missing values

    Returns
    -------
    dict
        Validation results containing:
        - 'valid': bool indicating if all checks passed
        - 'issues': list of identified issues
        - 'missing_values': Series of missing value proportions
        - 'duplicate_count': number of duplicate rows

    Examples
    --------
    >>> results = validate_data(df, required_columns=['id', 'value'])
    >>> if not results['valid']:
    ...     print(f"Issues found: {results['issues']}")
    """
    issues = []
    results = {'valid': True, 'issues': issues}

    # Check required columns
    if required_columns is not None:
        missing_cols = set(required_columns) - set(df.columns)
        if missing_cols:
            issues.append(f"Missing required columns: {missing_cols}")
            results['valid'] = False

    # Check for duplicates
    if check_duplicates:
        dup_count = df.duplicated().sum()
        results['duplicate_count'] = dup_count
        if dup_count > 0:
            issues.append(f"Found {dup_count} duplicate rows")

    # Check for missing values
    if check_missing:
        missing = check_missing_values(df, threshold=missing_threshold)
        results['missing_values'] = missing
        if len(missing) > 0:
            issues.append(f"Found missing values in {len(missing)} columns")

    return results


def check_data_types(
    df: pd.DataFrame,
    expected_types: Dict[str, str]
) -> Dict[str, any]:
    """
    Verify that columns have expected data types.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame
    expected_types : dict
        Dictionary mapping column names to expected data types

    Returns
    -------
    dict
        Results containing:
        - 'valid': bool
        - 'mismatches': dict of columns with incorrect types
    """
    mismatches = {}

    for col, expected_type in expected_types.items():
        if col not in df.columns:
            mismatches[col] = f"Column not found"
        elif df[col].dtype != expected_type:
            mismatches[col] = f"Expected {expected_type}, got {df[col].dtype}"

    return {
        'valid': len(mismatches) == 0,
        'mismatches': mismatches
    }
