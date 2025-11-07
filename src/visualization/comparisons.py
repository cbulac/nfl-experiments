"""
Comparison visualization utilities.
"""

from typing import Optional, Union, List, Tuple, Dict
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def plot_mean_comparison(
    groups: Dict[str, Union[np.ndarray, pd.Series]],
    title: str = "Mean Comparison",
    ylabel: str = "Mean Value",
    show_ci: bool = True,
    ci_level: float = 0.95,
    figsize: Tuple[int, int] = (10, 6)
) -> plt.Figure:
    """
    Plot comparison of means with confidence intervals.

    Parameters
    ----------
    groups : dict
        Dictionary mapping group names to data arrays
    title : str, default="Mean Comparison"
        Plot title
    ylabel : str, default="Mean Value"
        Y-axis label
    show_ci : bool, default=True
        Whether to show confidence intervals
    ci_level : float, default=0.95
        Confidence level for intervals
    figsize : tuple, default=(10, 6)
        Figure size

    Returns
    -------
    plt.Figure
        Matplotlib figure object
    """
    from scipy import stats

    fig, ax = plt.subplots(figsize=figsize)

    group_names = list(groups.keys())
    means = [np.mean(groups[name]) for name in group_names]

    if show_ci:
        ci_values = []
        for name in group_names:
            data = groups[name]
            ci = stats.t.interval(
                ci_level,
                len(data) - 1,
                loc=np.mean(data),
                scale=stats.sem(data)
            )
            ci_values.append((ci[1] - np.mean(data)))  # Half-width of CI

        ax.bar(group_names, means, yerr=ci_values, capsize=5, alpha=0.7, edgecolor='black')
    else:
        ax.bar(group_names, means, alpha=0.7, edgecolor='black')

    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    return fig


def plot_correlation_matrix(
    data: pd.DataFrame,
    title: str = "Correlation Matrix",
    method: str = 'pearson',
    figsize: Tuple[int, int] = (10, 8),
    annot: bool = True
) -> plt.Figure:
    """
    Plot correlation matrix heatmap.

    Parameters
    ----------
    data : pd.DataFrame
        Data to compute correlations
    title : str, default="Correlation Matrix"
        Plot title
    method : str, default='pearson'
        Correlation method: 'pearson', 'spearman', or 'kendall'
    figsize : tuple, default=(10, 8)
        Figure size
    annot : bool, default=True
        Whether to annotate cells with correlation values

    Returns
    -------
    plt.Figure
        Matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    corr_matrix = data.corr(method=method)

    sns.heatmap(
        corr_matrix,
        annot=annot,
        fmt='.2f',
        cmap='coolwarm',
        center=0,
        square=True,
        linewidths=1,
        cbar_kws={"shrink": 0.8},
        ax=ax
    )

    ax.set_title(title)
    plt.tight_layout()
    return fig


def plot_before_after(
    before: Union[np.ndarray, pd.Series],
    after: Union[np.ndarray, pd.Series],
    paired: bool = True,
    title: str = "Before vs After Comparison",
    labels: Optional[Tuple[str, str]] = None,
    figsize: Tuple[int, int] = (12, 5)
) -> plt.Figure:
    """
    Plot before-after comparison.

    Parameters
    ----------
    before : array-like
        Before measurements
    after : array-like
        After measurements
    paired : bool, default=True
        Whether measurements are paired
    title : str, default="Before vs After Comparison"
        Plot title
    labels : tuple of str, optional
        Labels for before and after
    figsize : tuple, default=(12, 5)
        Figure size

    Returns
    -------
    plt.Figure
        Matplotlib figure object
    """
    if labels is None:
        labels = ("Before", "After")

    if paired:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

        # Paired plot
        for i in range(len(before)):
            ax1.plot([0, 1], [before[i], after[i]], 'o-', alpha=0.5, color='gray')
        ax1.plot([0, 1], [np.mean(before), np.mean(after)], 'ro-', linewidth=3, label='Mean')
        ax1.set_xticks([0, 1])
        ax1.set_xticklabels(labels)
        ax1.set_ylabel("Value")
        ax1.set_title(f"{title} - Paired")
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Difference plot
        differences = after - before
        ax2.hist(differences, bins=20, edgecolor='black', alpha=0.7)
        ax2.axvline(x=0, color='r', linestyle='--', label='No change')
        ax2.axvline(x=np.mean(differences), color='g', linestyle='-', linewidth=2, label='Mean difference')
        ax2.set_xlabel("Difference (After - Before)")
        ax2.set_ylabel("Frequency")
        ax2.set_title("Distribution of Differences")
        ax2.legend()
        ax2.grid(True, alpha=0.3)
    else:
        fig, ax = plt.subplots(figsize=figsize)

        data_combined = pd.DataFrame({
            'Value': np.concatenate([before, after]),
            'Group': [labels[0]] * len(before) + [labels[1]] * len(after)
        })

        sns.boxplot(data=data_combined, x='Group', y='Value', ax=ax)
        ax.set_title(title)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_scatter_with_regression(
    x: Union[np.ndarray, pd.Series],
    y: Union[np.ndarray, pd.Series],
    title: str = "Scatter Plot with Regression",
    xlabel: str = "X",
    ylabel: str = "Y",
    show_ci: bool = True,
    figsize: Tuple[int, int] = (10, 6)
) -> plt.Figure:
    """
    Create scatter plot with regression line.

    Parameters
    ----------
    x : array-like
        X-axis data
    y : array-like
        Y-axis data
    title : str, default="Scatter Plot with Regression"
        Plot title
    xlabel : str, default="X"
        X-axis label
    ylabel : str, default="Y"
        Y-axis label
    show_ci : bool, default=True
        Whether to show confidence interval
    figsize : tuple, default=(10, 6)
        Figure size

    Returns
    -------
    plt.Figure
        Matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    sns.regplot(x=x, y=y, ax=ax, scatter_kws={'alpha': 0.5}, ci=95 if show_ci else None)

    # Calculate and display correlation
    from scipy.stats import pearsonr
    corr, p_value = pearsonr(x, y)
    ax.text(
        0.05, 0.95,
        f'r = {corr:.3f}\np = {p_value:.4f}',
        transform=ax.transAxes,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    )

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig
