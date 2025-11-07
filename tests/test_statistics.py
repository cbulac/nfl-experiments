"""
Unit tests for statistical utilities.
"""

import pytest
import sys
from pathlib import Path
import numpy as np

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.stats.hypothesis_tests import run_t_test, run_mann_whitney
from src.stats.effect_sizes import cohens_d, hedges_g
from src.stats.assumptions import check_normality, check_homogeneity


@pytest.fixture
def sample_groups():
    """Create sample groups for testing."""
    np.random.seed(42)
    group1 = np.random.normal(100, 15, 50)
    group2 = np.random.normal(110, 15, 50)
    return group1, group2


def test_t_test(sample_groups):
    """Test t-test functionality."""
    group1, group2 = sample_groups
    results = run_t_test(group1, group2)

    assert 'statistic' in results
    assert 'p_value' in results
    assert 'df' in results
    assert 'mean_diff' in results

    # Check that p_value is between 0 and 1
    assert 0 <= results['p_value'] <= 1

    # Check that degrees of freedom is correct
    assert results['df'] == len(group1) + len(group2) - 2


def test_mann_whitney(sample_groups):
    """Test Mann-Whitney U test."""
    group1, group2 = sample_groups
    results = run_mann_whitney(group1, group2)

    assert 'statistic' in results
    assert 'p_value' in results
    assert 0 <= results['p_value'] <= 1


def test_cohens_d(sample_groups):
    """Test Cohen's d calculation."""
    group1, group2 = sample_groups
    d = cohens_d(group1, group2)

    # Effect size should be a number
    assert isinstance(d, (int, float))

    # For our sample data, we expect a small to medium effect
    # (not testing exact value due to randomness, but checking reasonableness)
    assert -2 < d < 2


def test_hedges_g(sample_groups):
    """Test Hedges' g calculation."""
    group1, group2 = sample_groups
    g = hedges_g(group1, group2)

    # Should be similar to Cohen's d but slightly smaller
    d = cohens_d(group1, group2)
    assert isinstance(g, (int, float))
    assert abs(g) <= abs(d)  # Hedges' g is bias-corrected, typically smaller


def test_check_normality():
    """Test normality check."""
    np.random.seed(42)

    # Normal data
    normal_data = np.random.normal(0, 1, 100)
    results = check_normality(normal_data)

    assert 'statistic' in results
    assert 'p_value' in results
    assert 'is_normal' in results
    assert isinstance(results['is_normal'], bool)


def test_check_homogeneity(sample_groups):
    """Test homogeneity of variance check."""
    group1, group2 = sample_groups
    results = check_homogeneity(group1, group2)

    assert 'statistic' in results
    assert 'p_value' in results
    assert 'equal_variances' in results
    assert isinstance(results['equal_variances'], bool)


def test_equal_groups():
    """Test with identical groups (should have no difference)."""
    np.random.seed(42)
    group = np.random.normal(100, 15, 50)

    results = run_t_test(group, group)

    # P-value should be very close to 1 (no difference)
    assert results['p_value'] > 0.9
    assert abs(results['mean_diff']) < 1e-10  # Near zero


def test_different_sample_sizes():
    """Test with different sample sizes."""
    np.random.seed(42)
    group1 = np.random.normal(100, 15, 30)
    group2 = np.random.normal(100, 15, 50)

    results = run_t_test(group1, group2)

    assert results['df'] == 30 + 50 - 2
    assert 'p_value' in results
