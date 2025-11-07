"""
Effect size calculations for statistical tests.
"""

from typing import Union
import numpy as np
import pandas as pd
from scipy import stats


def cohens_d(
    group1: Union[np.ndarray, pd.Series],
    group2: Union[np.ndarray, pd.Series],
    pooled: bool = True
) -> float:
    """
    Calculate Cohen's d effect size for two groups.

    Parameters
    ----------
    group1 : array-like
        First group data
    group2 : array-like
        Second group data
    pooled : bool, default=True
        Use pooled standard deviation

    Returns
    -------
    float
        Cohen's d effect size

    Notes
    -----
    Interpretation guidelines:
    - Small effect: d = 0.2
    - Medium effect: d = 0.5
    - Large effect: d = 0.8

    Examples
    --------
    >>> d = cohens_d(treatment_group, control_group)
    >>> print(f"Effect size (Cohen's d): {d:.3f}")
    """
    n1, n2 = len(group1), len(group2)
    mean_diff = np.mean(group1) - np.mean(group2)

    if pooled:
        # Pooled standard deviation
        var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
        pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
        return mean_diff / pooled_std
    else:
        # Use control group standard deviation
        return mean_diff / np.std(group2, ddof=1)


def cramers_v(
    contingency_table: Union[np.ndarray, pd.DataFrame]
) -> float:
    """
    Calculate Cramér's V effect size for chi-square test.

    Parameters
    ----------
    contingency_table : array-like or DataFrame
        Contingency table of observed frequencies

    Returns
    -------
    float
        Cramér's V effect size (0 to 1)

    Notes
    -----
    Interpretation guidelines (for 2x2 tables):
    - Small effect: V = 0.1
    - Medium effect: V = 0.3
    - Large effect: V = 0.5
    """
    chi2, p, dof, expected = stats.chi2_contingency(contingency_table)
    n = np.sum(contingency_table)
    min_dim = min(contingency_table.shape) - 1

    return np.sqrt(chi2 / (n * min_dim))


def glass_delta(
    group1: Union[np.ndarray, pd.Series],
    group2: Union[np.ndarray, pd.Series]
) -> float:
    """
    Calculate Glass's Δ (delta) effect size.

    Uses control group standard deviation in denominator.

    Parameters
    ----------
    group1 : array-like
        Treatment/experimental group data
    group2 : array-like
        Control group data

    Returns
    -------
    float
        Glass's Δ effect size
    """
    mean_diff = np.mean(group1) - np.mean(group2)
    control_std = np.std(group2, ddof=1)

    return mean_diff / control_std


def hedges_g(
    group1: Union[np.ndarray, pd.Series],
    group2: Union[np.ndarray, pd.Series]
) -> float:
    """
    Calculate Hedges' g effect size (bias-corrected Cohen's d).

    Parameters
    ----------
    group1 : array-like
        First group data
    group2 : array-like
        Second group data

    Returns
    -------
    float
        Hedges' g effect size
    """
    d = cohens_d(group1, group2, pooled=True)
    n1, n2 = len(group1), len(group2)
    n = n1 + n2

    # Correction factor
    correction = 1 - (3 / (4 * n - 9))

    return d * correction


def calculate_effect_size(
    group1: Union[np.ndarray, pd.Series],
    group2: Union[np.ndarray, pd.Series],
    method: str = 'cohens_d'
) -> float:
    """
    Calculate effect size using specified method.

    Parameters
    ----------
    group1 : array-like
        First group data
    group2 : array-like
        Second group data
    method : str, default='cohens_d'
        Effect size method: 'cohens_d', 'hedges_g', or 'glass_delta'

    Returns
    -------
    float
        Calculated effect size
    """
    methods = {
        'cohens_d': cohens_d,
        'hedges_g': hedges_g,
        'glass_delta': glass_delta
    }

    if method not in methods:
        raise ValueError(f"Unknown method: {method}. Choose from {list(methods.keys())}")

    return methods[method](group1, group2)


def pearsons_r_to_cohens_d(r: float) -> float:
    """
    Convert Pearson's r to Cohen's d.

    Parameters
    ----------
    r : float
        Pearson's correlation coefficient

    Returns
    -------
    float
        Equivalent Cohen's d
    """
    return (2 * r) / np.sqrt(1 - r**2)


def cohens_d_to_pearsons_r(d: float) -> float:
    """
    Convert Cohen's d to Pearson's r.

    Parameters
    ----------
    d : float
        Cohen's d effect size

    Returns
    -------
    float
        Equivalent Pearson's r
    """
    return d / np.sqrt(d**2 + 4)
