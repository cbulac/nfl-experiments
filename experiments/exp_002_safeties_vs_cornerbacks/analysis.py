"""
Experiment 002: Safeties vs Cornerbacks Analysis
Main analysis script for hypothesis testing and comparisons.
"""

import sys
from pathlib import Path
import yaml
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parents[2]))

from src.stats.hypothesis_tests import run_t_test, run_chi_square
from src.stats.effect_sizes import cohens_d
from src.stats.assumptions import check_assumptions
from src.visualization.distributions import plot_distribution_comparison, plot_boxplot
from src.visualization.comparisons import plot_mean_comparison
from src.utils.logging import setup_logger
from src.utils.reporting import generate_report, save_results


def load_config(config_path: str = "config.yaml") -> dict:
    """Load experiment configuration."""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def setup_directories(config: dict) -> None:
    """Create output directories if they don't exist."""
    Path(config['output']['results_dir']).mkdir(parents=True, exist_ok=True)
    Path(config['output']['figures_dir']).mkdir(parents=True, exist_ok=True)
    Path(config['output']['log_dir']).mkdir(parents=True, exist_ok=True)


def load_data(config: dict, logger) -> pd.DataFrame:
    """Load engineered features dataset."""
    logger.info("Loading engineered features data...")
    data_path = Path(config['data']['engineered_features_file'])

    if not data_path.exists():
        raise FileNotFoundError(
            f"Engineered features file not found: {data_path}\n"
            "Please run scripts/load_and_merge_data.py and scripts/engineer_features.py first."
        )

    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} observations")
    logger.info(f"Position group distribution:\n{df['position_group'].value_counts()}")

    return df


def test_h1_positioning(df: pd.DataFrame, config: dict, logger) -> dict:
    """
    H1: Test if safeties are positioned farther from ball than cornerbacks.

    Parameters
    ----------
    df : pd.DataFrame
        Feature dataset
    config : dict
        Configuration
    logger : logging.Logger
        Logger instance

    Returns
    -------
    dict
        Test results
    """
    logger.info("\n" + "="*60)
    logger.info("H1: POSITIONING DIFFERENCES")
    logger.info("="*60)

    safeties = df[df['position_group'] == 'safeties']['initial_dist_to_ball'].dropna()
    cornerbacks = df[df['position_group'] == 'cornerbacks']['initial_dist_to_ball'].dropna()

    logger.info(f"Safeties: n={len(safeties)}, mean={safeties.mean():.2f}, std={safeties.std():.2f}")
    logger.info(f"Cornerbacks: n={len(cornerbacks)}, mean={cornerbacks.mean():.2f}, std={cornerbacks.std():.2f}")

    # Check assumptions
    assumptions = check_assumptions(safeties, cornerbacks, alpha=config['analysis']['statistical_tests']['alpha'])
    logger.info(f"\nAssumptions check: {assumptions['recommendation']}")

    # Run t-test (one-tailed: safeties > cornerbacks)
    test_result = run_t_test(
        safeties, cornerbacks,
        alternative='greater',
        equal_var=assumptions['homogeneity']['equal_variances']
    )

    # Calculate effect size
    effect_size = cohens_d(safeties, cornerbacks)

    logger.info(f"\nTest Results:")
    logger.info(f"  t-statistic: {test_result['statistic']:.3f}")
    logger.info(f"  p-value: {test_result['p_value']:.6f}")
    logger.info(f"  Cohen's d: {effect_size:.3f}")
    logger.info(f"  Mean difference: {test_result['mean_diff']:.2f} yards")

    # Interpretation
    alpha = config['analysis']['statistical_tests']['alpha']
    significant = test_result['p_value'] < alpha
    logger.info(f"\nConclusion: {'REJECT' if significant else 'FAIL TO REJECT'} null hypothesis (α={alpha})")

    return {
        'hypothesis': 'H1_positioning',
        'test_type': 't-test',
        'statistic': test_result['statistic'],
        'p_value': test_result['p_value'],
        'effect_size': effect_size,
        'mean_safeties': float(safeties.mean()),
        'mean_cornerbacks': float(cornerbacks.mean()),
        'mean_diff': test_result['mean_diff'],
        'significant': significant,
        'assumptions_met': assumptions['all_met']
    }


def test_h2_alignment(df: pd.DataFrame, config: dict, logger) -> dict:
    """
    H2: Test if safeties have better directional alignment than cornerbacks.

    Parameters
    ----------
    df : pd.DataFrame
        Feature dataset
    config : dict
        Configuration
    logger : logging.Logger
        Logger instance

    Returns
    -------
    dict
        Test results
    """
    logger.info("\n" + "="*60)
    logger.info("H2: DIRECTIONAL ALIGNMENT DIFFERENCES")
    logger.info("="*60)

    safeties = df[df['position_group'] == 'safeties']['avg_dir_alignment'].dropna()
    cornerbacks = df[df['position_group'] == 'cornerbacks']['avg_dir_alignment'].dropna()

    logger.info(f"Safeties: n={len(safeties)}, mean={safeties.mean():.2f}°, std={safeties.std():.2f}°")
    logger.info(f"Cornerbacks: n={len(cornerbacks)}, mean={cornerbacks.mean():.2f}°, std={cornerbacks.std():.2f}°")

    # Check assumptions
    assumptions = check_assumptions(safeties, cornerbacks, alpha=config['analysis']['statistical_tests']['alpha'])
    logger.info(f"\nAssumptions check: {assumptions['recommendation']}")

    # Run t-test (two-tailed)
    test_result = run_t_test(
        safeties, cornerbacks,
        alternative='two-sided',
        equal_var=assumptions['homogeneity']['equal_variances']
    )

    # Calculate effect size
    effect_size = cohens_d(safeties, cornerbacks)

    logger.info(f"\nTest Results:")
    logger.info(f"  t-statistic: {test_result['statistic']:.3f}")
    logger.info(f"  p-value: {test_result['p_value']:.6f}")
    logger.info(f"  Cohen's d: {effect_size:.3f}")
    logger.info(f"  Mean difference: {test_result['mean_diff']:.2f}°")

    # Interpretation
    alpha = config['analysis']['statistical_tests']['alpha']
    significant = test_result['p_value'] < alpha
    logger.info(f"\nConclusion: {'REJECT' if significant else 'FAIL TO REJECT'} null hypothesis (α={alpha})")

    return {
        'hypothesis': 'H2_alignment',
        'test_type': 't-test',
        'statistic': test_result['statistic'],
        'p_value': test_result['p_value'],
        'effect_size': effect_size,
        'mean_safeties': float(safeties.mean()),
        'mean_cornerbacks': float(cornerbacks.mean()),
        'mean_diff': test_result['mean_diff'],
        'significant': significant,
        'assumptions_met': assumptions['all_met']
    }


def test_h3_speed(df: pd.DataFrame, config: dict, logger) -> dict:
    """
    H3: Test if cornerbacks have higher speed than safeties.

    Parameters
    ----------
    df : pd.DataFrame
        Feature dataset
    config : dict
        Configuration
    logger : logging.Logger
        Logger instance

    Returns
    -------
    dict
        Test results
    """
    logger.info("\n" + "="*60)
    logger.info("H3: SPEED DIFFERENCES")
    logger.info("="*60)

    safeties = df[df['position_group'] == 'safeties']['avg_speed'].dropna()
    cornerbacks = df[df['position_group'] == 'cornerbacks']['avg_speed'].dropna()

    logger.info(f"Safeties: n={len(safeties)}, mean={safeties.mean():.2f} yd/s, std={safeties.std():.2f}")
    logger.info(f"Cornerbacks: n={len(cornerbacks)}, mean={cornerbacks.mean():.2f} yd/s, std={cornerbacks.std():.2f}")

    # Check assumptions
    assumptions = check_assumptions(safeties, cornerbacks, alpha=config['analysis']['statistical_tests']['alpha'])
    logger.info(f"\nAssumptions check: {assumptions['recommendation']}")

    # Run t-test (two-tailed)
    test_result = run_t_test(
        cornerbacks, safeties,  # Note: CB first to test CB > S
        alternative='greater',
        equal_var=assumptions['homogeneity']['equal_variances']
    )

    # Calculate effect size
    effect_size = cohens_d(cornerbacks, safeties)

    logger.info(f"\nTest Results:")
    logger.info(f"  t-statistic: {test_result['statistic']:.3f}")
    logger.info(f"  p-value: {test_result['p_value']:.6f}")
    logger.info(f"  Cohen's d: {effect_size:.3f}")
    logger.info(f"  Mean difference: {test_result['mean_diff']:.2f} yd/s")

    # Interpretation
    alpha = config['analysis']['statistical_tests']['alpha']
    significant = test_result['p_value'] < alpha
    logger.info(f"\nConclusion: {'REJECT' if significant else 'FAIL TO REJECT'} null hypothesis (α={alpha})")

    return {
        'hypothesis': 'H3_speed',
        'test_type': 't-test',
        'statistic': test_result['statistic'],
        'p_value': test_result['p_value'],
        'effect_size': effect_size,
        'mean_safeties': float(safeties.mean()),
        'mean_cornerbacks': float(cornerbacks.mean()),
        'mean_diff': test_result['mean_diff'],
        'significant': significant,
        'assumptions_met': assumptions['all_met']
    }


def generate_visualizations(df: pd.DataFrame, config: dict, logger) -> None:
    """
    Generate comparison visualizations.

    Parameters
    ----------
    df : pd.DataFrame
        Feature dataset
    config : dict
        Configuration
    logger : logging.Logger
        Logger instance
    """
    logger.info("\n" + "="*60)
    logger.info("GENERATING VISUALIZATIONS")
    logger.info("="*60)

    figures_dir = Path(config['output']['figures_dir'])
    sns.set_style(config['visualization']['style'])

    # 1. Distance comparison
    logger.info("Creating distance comparison plot...")
    safeties_dist = df[df['position_group'] == 'safeties']['initial_dist_to_ball'].dropna()
    cbs_dist = df[df['position_group'] == 'cornerbacks']['initial_dist_to_ball'].dropna()

    fig = plot_distribution_comparison(
        safeties_dist, cbs_dist,
        labels=('Safeties', 'Cornerbacks'),
        title='Initial Distance to Ball Landing Location',
        xlabel='Distance (yards)',
        figsize=config['visualization']['figure_sizes']['comparison_plot']
    )
    plt.savefig(figures_dir / config['output']['figure_names']['distance_comparison'],
                dpi=config['visualization']['dpi'], bbox_inches='tight')
    plt.close()

    # 2. Speed comparison
    logger.info("Creating speed comparison plot...")
    safeties_speed = df[df['position_group'] == 'safeties']['avg_speed'].dropna()
    cbs_speed = df[df['position_group'] == 'cornerbacks']['avg_speed'].dropna()

    fig = plot_distribution_comparison(
        safeties_speed, cbs_speed,
        labels=('Safeties', 'Cornerbacks'),
        title='Average Speed During Pre-Throw Frames',
        xlabel='Speed (yards/second)',
        figsize=config['visualization']['figure_sizes']['comparison_plot']
    )
    plt.savefig(figures_dir / config['output']['figure_names']['speed_comparison'],
                dpi=config['visualization']['dpi'], bbox_inches='tight')
    plt.close()

    # 3. Alignment comparison
    logger.info("Creating alignment comparison plot...")
    safeties_align = df[df['position_group'] == 'safeties']['avg_dir_alignment'].dropna()
    cbs_align = df[df['position_group'] == 'cornerbacks']['avg_dir_alignment'].dropna()

    fig = plot_distribution_comparison(
        safeties_align, cbs_align,
        labels=('Safeties', 'Cornerbacks'),
        title='Directional Alignment to Ball (Lower = Better)',
        xlabel='Angular Difference (degrees)',
        figsize=config['visualization']['figure_sizes']['comparison_plot']
    )
    plt.savefig(figures_dir / config['output']['figure_names']['alignment_comparison'],
                dpi=config['visualization']['dpi'], bbox_inches='tight')
    plt.close()

    logger.info(f"Visualizations saved to {figures_dir}")


def main():
    """Main analysis pipeline."""
    # Load configuration
    config = load_config()

    # Setup
    setup_directories(config)
    logger = setup_logger(
        log_dir=config['output']['log_dir'],
        experiment_name=config['experiment']['name']
    )

    logger.info("="*60)
    logger.info(f"Starting experiment: {config['experiment']['name']}")
    logger.info("="*60)

    try:
        # Load data
        df = load_data(config, logger)

        # Run hypothesis tests
        results = {
            'experiment': config['experiment']['name'],
            'date': datetime.now().isoformat(),
            'sample_size': {
                'total': len(df),
                'safeties': len(df[df['position_group'] == 'safeties']),
                'cornerbacks': len(df[df['position_group'] == 'cornerbacks'])
            },
            'hypothesis_tests': {}
        }

        # H1: Positioning
        results['hypothesis_tests']['H1'] = test_h1_positioning(df, config, logger)

        # H2: Alignment
        results['hypothesis_tests']['H2'] = test_h2_alignment(df, config, logger)

        # H3: Speed
        results['hypothesis_tests']['H3'] = test_h3_speed(df, config, logger)

        # Generate visualizations
        generate_visualizations(df, config, logger)

        # Save results
        results_file = Path(config['output']['results_dir']) / 'statistics.json'
        save_results(results, results_file, format='json')

        logger.info("\n" + "="*60)
        logger.info("ANALYSIS SUMMARY")
        logger.info("="*60)
        for hyp_name, hyp_results in results['hypothesis_tests'].items():
            logger.info(f"\n{hyp_name} ({hyp_results['hypothesis']}):")
            logger.info(f"  p-value: {hyp_results['p_value']:.6f}")
            logger.info(f"  Effect size: {hyp_results['effect_size']:.3f}")
            logger.info(f"  Significant: {hyp_results['significant']}")

        logger.info("\n" + "="*60)
        logger.info("Analysis complete!")

    except Exception as e:
        logger.error(f"Error during analysis: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
