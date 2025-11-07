"""
Distribution visualization utilities.
"""

from typing import Optional, Union, List, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def plot_distribution(
    data: Union[np.ndarray, pd.Series],
    title: str = "Distribution",
    xlabel: str = "Value",
    bins: int = 30,
    kde: bool = True,
    figsize: Tuple[int, int] = (10, 6)
) -> plt.Figure:
    """
    Plot distribution of a single variable.

    Parameters
    ----------
    data : array-like or Series
        Data to plot
    title : str, default="Distribution"
        Plot title
    xlabel : str, default="Value"
        X-axis label
    bins : int, default=30
        Number of histogram bins
    kde : bool, default=True
        Whether to overlay kernel density estimate
    figsize : tuple, default=(10, 6)
        Figure size

    Returns
    -------
    plt.Figure
        Matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    if kde:
        sns.histplot(data, bins=bins, kde=True, ax=ax)
    else:
        ax.hist(data, bins=bins, edgecolor='black', alpha=0.7)

    ax.set_xlabel(xlabel)
    ax.set_ylabel("Frequency")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_distribution_comparison(
    group1: Union[np.ndarray, pd.Series],
    group2: Union[np.ndarray, pd.Series],
    labels: Optional[Tuple[str, str]] = None,
    title: str = "Distribution Comparison",
    xlabel: str = "Value",
    bins: int = 30,
    figsize: Tuple[int, int] = (12, 6)
) -> plt.Figure:
    """
    Plot comparison of two distributions.

    Parameters
    ----------
    group1 : array-like
        First group data
    group2 : array-like
        Second group data
    labels : tuple of str, optional
        Labels for the two groups
    title : str, default="Distribution Comparison"
        Plot title
    xlabel : str, default="Value"
        X-axis label
    bins : int, default=30
        Number of histogram bins
    figsize : tuple, default=(12, 6)
        Figure size

    Returns
    -------
    plt.Figure
        Matplotlib figure object
    """
    if labels is None:
        labels = ("Group 1", "Group 2")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    # Histograms with KDE
    sns.histplot(group1, bins=bins, kde=True, ax=ax1, label=labels[0], color='blue', alpha=0.6)
    sns.histplot(group2, bins=bins, kde=True, ax=ax1, label=labels[1], color='red', alpha=0.6)
    ax1.set_xlabel(xlabel)
    ax1.set_ylabel("Frequency")
    ax1.set_title(f"{title} - Overlaid")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Box plots
    data_combined = pd.DataFrame({
        'Value': np.concatenate([group1, group2]),
        'Group': [labels[0]] * len(group1) + [labels[1]] * len(group2)
    })
    sns.boxplot(data=data_combined, x='Group', y='Value', ax=ax2)
    ax2.set_title(f"{title} - Box Plots")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_boxplot(
    data: Union[pd.DataFrame, dict],
    title: str = "Box Plot Comparison",
    ylabel: str = "Value",
    figsize: Tuple[int, int] = (10, 6)
) -> plt.Figure:
    """
    Create box plots for multiple groups.

    Parameters
    ----------
    data : DataFrame or dict
        Data to plot. If DataFrame, each column is a group.
        If dict, keys are group names and values are data arrays.
    title : str, default="Box Plot Comparison"
        Plot title
    ylabel : str, default="Value"
        Y-axis label
    figsize : tuple, default=(10, 6)
        Figure size

    Returns
    -------
    plt.Figure
        Matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    if isinstance(data, dict):
        data = pd.DataFrame(data)

    sns.boxplot(data=data, ax=ax)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    return fig


def plot_qq(
    data: Union[np.ndarray, pd.Series],
    title: str = "Q-Q Plot",
    figsize: Tuple[int, int] = (8, 8)
) -> plt.Figure:
    """
    Create Q-Q plot to assess normality.

    Parameters
    ----------
    data : array-like
        Data to plot
    title : str, default="Q-Q Plot"
        Plot title
    figsize : tuple, default=(8, 8)
        Figure size

    Returns
    -------
    plt.Figure
        Matplotlib figure object
    """
    from scipy import stats as sp_stats

    fig, ax = plt.subplots(figsize=figsize)

    sp_stats.probplot(data, dist="norm", plot=ax)
    ax.set_title(title)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_violin(
    data: Union[pd.DataFrame, dict],
    title: str = "Violin Plot Comparison",
    ylabel: str = "Value",
    figsize: Tuple[int, int] = (10, 6)
) -> plt.Figure:
    """
    Create violin plots for multiple groups.

    Parameters
    ----------
    data : DataFrame or dict
        Data to plot
    title : str, default="Violin Plot Comparison"
        Plot title
    ylabel : str, default="Value"
        Y-axis label
    figsize : tuple, default=(10, 6)
        Figure size

    Returns
    -------
    plt.Figure
        Matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    if isinstance(data, dict):
        data = pd.DataFrame(data)

    sns.violinplot(data=data, ax=ax)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    return fig
