"""
Statistical assumption checking utilities.
"""

from typing import Dict, Union, List
import numpy as np
import pandas as pd
from scipy import stats


def check_normality(
    data: Union[np.ndarray, pd.Series],
    method: str = 'shapiro',
    alpha: float = 0.05
) -> Dict[str, Union[float, bool]]:
    """
    Test for normality of data distribution.

    Parameters
    ----------
    data : array-like
        Data to test
    method : str, default='shapiro'
        Test method: 'shapiro' (Shapiro-Wilk) or 'kstest' (Kolmogorov-Smirnov)
    alpha : float, default=0.05
        Significance level

    Returns
    -------
    dict
        Results containing:
        - 'statistic': test statistic
        - 'p_value': p-value
        - 'is_normal': True if data appears normally distributed
        - 'method': test method used

    Examples
    --------
    >>> results = check_normality(data)
    >>> if results['is_normal']:
    ...     print("Data is normally distributed")
    """
    if method == 'shapiro':
        statistic, p_value = stats.shapiro(data)
    elif method == 'kstest':
        statistic, p_value = stats.kstest(data, 'norm')
    else:
        raise ValueError(f"Unknown method: {method}")

    return {
        'statistic': float(statistic),
        'p_value': float(p_value),
        'is_normal': p_value > alpha,
        'method': method
    }


def check_homogeneity(
    *groups: Union[np.ndarray, pd.Series],
    alpha: float = 0.05
) -> Dict[str, Union[float, bool]]:
    """
    Test for homogeneity of variances (Levene's test).

    Parameters
    ----------
    *groups : array-like
        Two or more groups to compare
    alpha : float, default=0.05
        Significance level

    Returns
    -------
    dict
        Results containing:
        - 'statistic': Levene's test statistic
        - 'p_value': p-value
        - 'equal_variances': True if variances appear equal
    """
    statistic, p_value = stats.levene(*groups)

    return {
        'statistic': float(statistic),
        'p_value': float(p_value),
        'equal_variances': p_value > alpha
    }


def check_independence(
    data: Union[np.ndarray, pd.Series],
    lag: int = 1
) -> Dict[str, Union[float, bool]]:
    """
    Check for independence using Durbin-Watson test.

    Parameters
    ----------
    data : array-like
        Data to test
    lag : int, default=1
        Lag for autocorrelation

    Returns
    -------
    dict
        Results containing:
        - 'dw_statistic': Durbin-Watson statistic
        - 'likely_independent': rough assessment (DW near 2.0 suggests independence)

    Notes
    -----
    Durbin-Watson statistic ranges from 0 to 4:
    - 2.0: no autocorrelation
    - 0: perfect positive autocorrelation
    - 4: perfect negative autocorrelation
    """
    residuals = np.diff(data, n=lag)
    dw_stat = np.sum(np.diff(residuals)**2) / np.sum(residuals**2)

    return {
        'dw_statistic': float(dw_stat),
        'likely_independent': 1.5 < dw_stat < 2.5  # Rough heuristic
    }


def check_assumptions(
    group1: Union[np.ndarray, pd.Series],
    group2: Union[np.ndarray, pd.Series],
    alpha: float = 0.05
) -> Dict[str, Dict]:
    """
    Check common assumptions for parametric tests (e.g., t-test).

    Parameters
    ----------
    group1 : array-like
        First group data
    group2 : array-like
        Second group data
    alpha : float, default=0.05
        Significance level

    Returns
    -------
    dict
        Comprehensive results containing:
        - 'normality_group1': normality test for group 1
        - 'normality_group2': normality test for group 2
        - 'homogeneity': homogeneity of variance test
        - 'all_met': True if all assumptions are met
        - 'recommendation': suggested test based on assumptions

    Examples
    --------
    >>> results = check_assumptions(group_a, group_b)
    >>> print(results['recommendation'])
    """
    norm1 = check_normality(group1, alpha=alpha)
    norm2 = check_normality(group2, alpha=alpha)
    homog = check_homogeneity(group1, group2, alpha=alpha)

    all_met = (
        norm1['is_normal'] and
        norm2['is_normal'] and
        homog['equal_variances']
    )

    # Provide recommendation
    if all_met:
        recommendation = "Use standard t-test (assumptions met)"
    elif not (norm1['is_normal'] and norm2['is_normal']):
        recommendation = "Use Mann-Whitney U test (normality violated)"
    elif not homog['equal_variances']:
        recommendation = "Use Welch's t-test (unequal variances)"
    else:
        recommendation = "Review assumptions carefully"

    return {
        'normality_group1': norm1,
        'normality_group2': norm2,
        'homogeneity': homog,
        'all_met': all_met,
        'recommendation': recommendation
    }


def qq_plot_data(
    data: Union[np.ndarray, pd.Series]
) -> Dict[str, np.ndarray]:
    """
    Generate Q-Q plot data for assessing normality.

    Parameters
    ----------
    data : array-like
        Data to analyze

    Returns
    -------
    dict
        Dictionary containing:
        - 'theoretical_quantiles': expected quantiles from normal distribution
        - 'sample_quantiles': observed quantiles from data
    """
    sorted_data = np.sort(data)
    n = len(sorted_data)
    theoretical_quantiles = stats.norm.ppf(np.linspace(0.01, 0.99, n))

    return {
        'theoretical_quantiles': theoretical_quantiles,
        'sample_quantiles': sorted_data
    }
