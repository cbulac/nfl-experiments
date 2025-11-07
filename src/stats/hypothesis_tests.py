"""
Statistical hypothesis testing utilities.
"""

from typing import Dict, Optional, Union
import numpy as np
import pandas as pd
from scipy import stats


def run_t_test(
    group1: Union[np.ndarray, pd.Series],
    group2: Union[np.ndarray, pd.Series],
    alternative: str = 'two-sided',
    equal_var: bool = True
) -> Dict[str, float]:
    """
    Perform independent samples t-test.

    Parameters
    ----------
    group1 : array-like
        First group data
    group2 : array-like
        Second group data
    alternative : str, default='two-sided'
        Alternative hypothesis: 'two-sided', 'less', or 'greater'
    equal_var : bool, default=True
        Assume equal variances (True for standard t-test, False for Welch's)

    Returns
    -------
    dict
        Results containing:
        - 'statistic': test statistic
        - 'p_value': p-value
        - 'df': degrees of freedom
        - 'mean_diff': difference in means

    Examples
    --------
    >>> results = run_t_test(group_a, group_b)
    >>> print(f"p-value: {results['p_value']:.4f}")
    """
    statistic, p_value = stats.ttest_ind(
        group1, group2,
        equal_var=equal_var,
        alternative=alternative
    )

    df = len(group1) + len(group2) - 2

    return {
        'statistic': float(statistic),
        'p_value': float(p_value),
        'df': df,
        'mean_diff': float(np.mean(group1) - np.mean(group2))
    }


def run_mann_whitney(
    group1: Union[np.ndarray, pd.Series],
    group2: Union[np.ndarray, pd.Series],
    alternative: str = 'two-sided'
) -> Dict[str, float]:
    """
    Perform Mann-Whitney U test (non-parametric alternative to t-test).

    Parameters
    ----------
    group1 : array-like
        First group data
    group2 : array-like
        Second group data
    alternative : str, default='two-sided'
        Alternative hypothesis: 'two-sided', 'less', or 'greater'

    Returns
    -------
    dict
        Results containing:
        - 'statistic': U statistic
        - 'p_value': p-value
    """
    statistic, p_value = stats.mannwhitneyu(
        group1, group2,
        alternative=alternative
    )

    return {
        'statistic': float(statistic),
        'p_value': float(p_value)
    }


def run_chi_square(
    contingency_table: Union[np.ndarray, pd.DataFrame]
) -> Dict[str, float]:
    """
    Perform chi-square test of independence.

    Parameters
    ----------
    contingency_table : array-like or DataFrame
        Contingency table of observed frequencies

    Returns
    -------
    dict
        Results containing:
        - 'statistic': chi-square statistic
        - 'p_value': p-value
        - 'df': degrees of freedom
        - 'expected': expected frequencies
    """
    statistic, p_value, df, expected = stats.chi2_contingency(contingency_table)

    return {
        'statistic': float(statistic),
        'p_value': float(p_value),
        'df': int(df),
        'expected': expected
    }


def run_anova(
    *groups: Union[np.ndarray, pd.Series]
) -> Dict[str, float]:
    """
    Perform one-way ANOVA.

    Parameters
    ----------
    *groups : array-like
        Variable number of group arrays

    Returns
    -------
    dict
        Results containing:
        - 'statistic': F statistic
        - 'p_value': p-value
    """
    statistic, p_value = stats.f_oneway(*groups)

    return {
        'statistic': float(statistic),
        'p_value': float(p_value)
    }


def run_paired_t_test(
    before: Union[np.ndarray, pd.Series],
    after: Union[np.ndarray, pd.Series],
    alternative: str = 'two-sided'
) -> Dict[str, float]:
    """
    Perform paired samples t-test.

    Parameters
    ----------
    before : array-like
        Measurements before treatment
    after : array-like
        Measurements after treatment
    alternative : str, default='two-sided'
        Alternative hypothesis: 'two-sided', 'less', or 'greater'

    Returns
    -------
    dict
        Results containing:
        - 'statistic': t statistic
        - 'p_value': p-value
        - 'mean_diff': mean difference
    """
    statistic, p_value = stats.ttest_rel(
        before, after,
        alternative=alternative
    )

    return {
        'statistic': float(statistic),
        'p_value': float(p_value),
        'mean_diff': float(np.mean(after - before))
    }
