"""
Experiment 003: Help Defenders vs Primary Defenders
Test whether help defenders have higher interception success rates than primary defenders.
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
from scipy import stats as sp_stats

# Add src to path
sys.path.append(str(Path(__file__).parents[2]))

from src.stats.hypothesis_tests import run_t_test, run_chi_square
from src.stats.effect_sizes import cohens_d
from src.utils.logging import setup_logger
from src.utils.reporting import save_results


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
    """Load engineered features from previous experiment."""
    logger.info("Loading engineered features...")
    data_path = Path(config['data']['input_file'])

    if not data_path.exists():
        raise FileNotFoundError(f"Input file not found: {data_path}")

    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} observations from {data_path.name}")

    return df


def classify_defender_type(df: pd.DataFrame, config: dict, logger) -> pd.DataFrame:
    """
    Classify each defender as primary or help based on proximity to ball.

    Parameters
    ----------
    df : pd.DataFrame
        Input data
    config : dict
        Configuration
    logger : logging.Logger
        Logger instance

    Returns
    -------
    pd.DataFrame
        Data with defender_type column added
    """
    logger.info("Classifying defenders as primary or help...")

    method = config['defender_classification']['method']
    logger.info(f"Using method: {method}")

    if method == "proximity_rank":
        # Rank defenders by distance to ball (within each play)
        df['proximity_rank'] = df.groupby(['game_id', 'play_id'])['initial_dist_to_ball'].rank(method='first')

        primary_rank = config['defender_classification']['proximity_rank']['primary_rank']
        df['defender_type'] = df['proximity_rank'].apply(
            lambda x: 'primary' if x == primary_rank else 'help'
        )

        logger.info(f"Primary defenders: rank = {primary_rank}")
        logger.info(f"Help defenders: rank > {primary_rank}")

    elif method == "distance_threshold":
        threshold = config['defender_classification']['distance_threshold']['primary_max_distance']
        df['defender_type'] = df['initial_dist_to_ball'].apply(
            lambda x: 'primary' if x <= threshold else 'help'
        )

        logger.info(f"Primary defenders: ≤ {threshold} yards from ball")
        logger.info(f"Help defenders: > {threshold} yards from ball")

    # Log distribution
    logger.info(f"\nDefender type distribution:")
    logger.info(df['defender_type'].value_counts())
    logger.info(f"\nDefenders per play:")
    defenders_per_play = df.groupby(['game_id', 'play_id'])['defender_type'].value_counts().unstack(fill_value=0)
    logger.info(f"  Mean primary per play: {defenders_per_play['primary'].mean():.2f}")
    logger.info(f"  Mean help per play: {defenders_per_play['help'].mean():.2f}")

    return df


def identify_interceptions(df: pd.DataFrame, config: dict, logger) -> pd.DataFrame:
    """
    Identify which players made interceptions.

    Parameters
    ----------
    df : pd.DataFrame
        Input data
    config : dict
        Configuration
    logger : logging.Logger
        Logger instance

    Returns
    -------
    pd.DataFrame
        Data with made_interception column added
    """
    logger.info("Identifying interceptions...")

    method = config['interception_identification']['method']

    if method == "player_to_predict" and 'player_to_predict' in df.columns:
        # Use player_to_predict flag from original data
        df['made_interception'] = df['player_to_predict'].astype(int)
        logger.info("Using player_to_predict column")
    else:
        # Use final proximity as proxy
        logger.info("Using final proximity as proxy for interception (player_to_predict not in features)")

        if 'final_proximity_to_ball' in df.columns:
            # Player closest to ball at end is assumed to have made interception
            df['made_interception'] = (
                df.groupby(['game_id', 'play_id'])['final_proximity_to_ball']
                .transform(lambda x: x == x.min() if x.notna().any() else False)
            ).astype(int)

            # Handle NaN values (plays without post-throw data)
            df['made_interception'] = df['made_interception'].fillna(0).astype(int)
        else:
            # Fallback: assume only one INT per play, assign to primary defender
            logger.warning("No final_proximity_to_ball column - assuming primary defender made INT")
            df['made_interception'] = (df['defender_type'] == 'primary').astype(int)

    # Log interception statistics
    total_ints = df['made_interception'].sum()
    total_plays = df[['game_id', 'play_id']].drop_duplicates().shape[0]

    logger.info(f"\nInterception identification:")
    logger.info(f"  Total interceptions identified: {total_ints}")
    logger.info(f"  Total plays: {total_plays}")
    logger.info(f"  Interceptions per play: {total_ints / total_plays:.2f}")

    logger.info(f"\nInterceptions by defender type:")
    logger.info(df.groupby('defender_type')['made_interception'].sum())

    return df


def calculate_interception_rates(df: pd.DataFrame, logger) -> dict:
    """
    Calculate interception rates by defender type.

    Parameters
    ----------
    df : pd.DataFrame
        Data with defender types and interceptions
    logger : logging.Logger
        Logger instance

    Returns
    -------
    dict
        Interception rates and statistics
    """
    logger.info("\n" + "="*60)
    logger.info("CALCULATING INTERCEPTION RATES")
    logger.info("="*60)

    results = {}

    for def_type in ['primary', 'help']:
        subset = df[df['defender_type'] == def_type]
        n_total = len(subset)
        n_int = subset['made_interception'].sum()
        rate = n_int / n_total if n_total > 0 else 0

        results[def_type] = {
            'n_total': int(n_total),
            'n_interceptions': int(n_int),
            'interception_rate': float(rate)
        }

        logger.info(f"\n{def_type.upper()} Defenders:")
        logger.info(f"  Total observations: {n_total:,}")
        logger.info(f"  Interceptions: {n_int}")
        logger.info(f"  Interception rate: {rate:.1%}")

    # Calculate odds ratio
    primary_rate = results['primary']['interception_rate']
    help_rate = results['help']['interception_rate']

    if primary_rate > 0 and primary_rate < 1:
        odds_primary = primary_rate / (1 - primary_rate)
        odds_help = help_rate / (1 - help_rate)
        odds_ratio = odds_help / odds_primary if odds_primary > 0 else np.nan

        results['odds_ratio'] = float(odds_ratio)
        results['relative_risk'] = float(help_rate / primary_rate) if primary_rate > 0 else np.nan

        logger.info(f"\nOdds Ratio (Help vs Primary): {odds_ratio:.3f}")
        logger.info(f"Relative Risk (Help vs Primary): {results['relative_risk']:.3f}")

    return results


def test_h1_interception_rate(df: pd.DataFrame, config: dict, logger) -> dict:
    """
    H1: Test if help defenders have higher interception rates.

    Parameters
    ----------
    df : pd.DataFrame
        Data
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
    logger.info("H1: INTERCEPTION RATE BY DEFENDER TYPE")
    logger.info("="*60)

    # Create contingency table
    contingency = pd.crosstab(
        df['defender_type'],
        df['made_interception'],
        margins=True
    )

    logger.info("\nContingency Table:")
    logger.info(contingency)

    # Extract values for 2x2 table (excluding margins)
    table_2x2 = contingency.iloc[:2, :2].values

    # Chi-square test
    chi2_result = run_chi_square(table_2x2)

    logger.info(f"\nChi-Square Test:")
    logger.info(f"  χ² statistic: {chi2_result['statistic']:.3f}")
    logger.info(f"  p-value: {chi2_result['p_value']:.6f}")
    logger.info(f"  df: {chi2_result['df']}")

    # Two-proportion z-test (more appropriate for one-tailed)
    primary_successes = df[(df['defender_type'] == 'primary')]['made_interception'].sum()
    primary_total = len(df[df['defender_type'] == 'primary'])
    help_successes = df[(df['defender_type'] == 'help')]['made_interception'].sum()
    help_total = len(df[df['defender_type'] == 'help'])

    # Manual z-test
    p1 = primary_successes / primary_total
    p2 = help_successes / help_total
    p_pooled = (primary_successes + help_successes) / (primary_total + help_total)

    se = np.sqrt(p_pooled * (1 - p_pooled) * (1/primary_total + 1/help_total))
    z_stat = (p2 - p1) / se
    p_value_one_tailed = 1 - sp_stats.norm.cdf(z_stat)  # One-tailed: help > primary

    logger.info(f"\nTwo-Proportion Z-Test (one-tailed):")
    logger.info(f"  z-statistic: {z_stat:.3f}")
    logger.info(f"  p-value (help > primary): {p_value_one_tailed:.6f}")

    alpha = config['analysis']['statistical_tests']['alpha']
    significant = p_value_one_tailed < alpha

    logger.info(f"\nConclusion: {'REJECT' if significant else 'FAIL TO REJECT'} null hypothesis (α={alpha})")

    return {
        'hypothesis': 'H1_interception_rate',
        'test_type': 'chi_square_and_proportion_test',
        'chi2_statistic': chi2_result['statistic'],
        'chi2_p_value': chi2_result['p_value'],
        'z_statistic': float(z_stat),
        'p_value_one_tailed': float(p_value_one_tailed),
        'primary_rate': float(p1),
        'help_rate': float(p2),
        'rate_difference': float(p2 - p1),
        'significant': significant
    }


def test_h2_proximity(df: pd.DataFrame, config: dict, logger) -> dict:
    """
    H2: Test if primary defenders are closer to ball.
    """
    logger.info("\n" + "="*60)
    logger.info("H2: PROXIMITY DIFFERENCES")
    logger.info("="*60)

    primary = df[df['defender_type'] == 'primary']['initial_dist_to_ball'].dropna()
    help_def = df[df['defender_type'] == 'help']['initial_dist_to_ball'].dropna()

    logger.info(f"Primary: n={len(primary)}, mean={primary.mean():.2f} yards")
    logger.info(f"Help: n={len(help_def)}, mean={help_def.mean():.2f} yards")

    test_result = run_t_test(primary, help_def, alternative='less')
    effect_size = cohens_d(primary, help_def)

    logger.info(f"\nt-statistic: {test_result['statistic']:.3f}")
    logger.info(f"p-value (primary < help): {test_result['p_value']:.6f}")
    logger.info(f"Cohen's d: {effect_size:.3f}")

    alpha = config['analysis']['statistical_tests']['alpha']
    significant = test_result['p_value'] < alpha

    logger.info(f"\nConclusion: {'REJECT' if significant else 'FAIL TO REJECT'} null hypothesis (α={alpha})")

    return {
        'hypothesis': 'H2_proximity',
        'test_type': 't-test',
        'statistic': test_result['statistic'],
        'p_value': test_result['p_value'],
        'effect_size': effect_size,
        'mean_primary': float(primary.mean()),
        'mean_help': float(help_def.mean()),
        'mean_diff': test_result['mean_diff'],
        'significant': significant
    }


def generate_visualizations(df: pd.DataFrame, config: dict, logger) -> None:
    """Generate comparison visualizations."""
    logger.info("\n" + "="*60)
    logger.info("GENERATING VISUALIZATIONS")
    logger.info("="*60)

    figures_dir = Path(config['output']['figures_dir'])
    sns.set_style(config['visualization']['style'])
    colors = config['visualization']['defender_type_colors']

    # 1. Interception rates bar plot
    logger.info("Creating interception rates plot...")
    rates = df.groupby('defender_type')['made_interception'].agg(['sum', 'count', 'mean'])
    rates['rate_pct'] = rates['mean'] * 100

    fig, ax = plt.subplots(figsize=config['visualization']['figure_sizes']['bar_plot'])
    bars = ax.bar(rates.index, rates['rate_pct'],
                   color=[colors['primary'], colors['help']],
                   edgecolor='black', alpha=0.7)

    # Add value labels
    for bar, val, n in zip(bars, rates['rate_pct'], rates['sum']):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.1f}%\n(n={int(n)})',
                ha='center', va='bottom')

    ax.set_ylabel('Interception Rate (%)')
    ax.set_xlabel('Defender Type')
    ax.set_title('Interception Success Rate by Defender Type')
    ax.set_ylim(0, max(rates['rate_pct']) * 1.2)
    plt.tight_layout()
    plt.savefig(figures_dir / config['visualization']['figure_names']['interception_rates'],
                dpi=config['visualization']['dpi'], bbox_inches='tight')
    plt.close()

    # 2. Proximity comparison
    logger.info("Creating proximity comparison plot...")
    fig, ax = plt.subplots(figsize=config['visualization']['figure_sizes']['comparison_plot'])

    primary_dist = df[df['defender_type'] == 'primary']['initial_dist_to_ball'].dropna()
    help_dist = df[df['defender_type'] == 'help']['initial_dist_to_ball'].dropna()

    positions = [1, 2]
    bp = ax.boxplot([primary_dist, help_dist], positions=positions,
                     widths=0.6, patch_artist=True,
                     labels=['Primary', 'Help'])

    for patch, color in zip(bp['boxes'], [colors['primary'], colors['help']]):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax.set_ylabel('Distance to Ball (yards)')
    ax.set_xlabel('Defender Type')
    ax.set_title('Initial Distance to Ball Landing Location')
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(figures_dir / config['visualization']['figure_names']['proximity_comparison'],
                dpi=config['visualization']['dpi'], bbox_inches='tight')
    plt.close()

    logger.info(f"Visualizations saved to {figures_dir}")


def main():
    """Main analysis pipeline."""
    config = load_config()

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

        # Classify defender types
        df = classify_defender_type(df, config, logger)

        # Identify interceptions
        df = identify_interceptions(df, config, logger)

        # Calculate descriptive statistics
        int_rates = calculate_interception_rates(df, logger)

        # Run hypothesis tests
        results = {
            'experiment': config['experiment']['name'],
            'date': datetime.now().isoformat(),
            'sample_size': {
                'total': len(df),
                'primary_defenders': int(df[df['defender_type'] == 'primary'].shape[0]),
                'help_defenders': int(df[df['defender_type'] == 'help'].shape[0])
            },
            'interception_rates': int_rates,
            'hypothesis_tests': {}
        }

        # H1: Interception rate
        results['hypothesis_tests']['H1'] = test_h1_interception_rate(df, config, logger)

        # H2: Proximity
        results['hypothesis_tests']['H2'] = test_h2_proximity(df, config, logger)

        # Generate visualizations
        generate_visualizations(df, config, logger)

        # Save results
        results_file = Path(config['output']['statistics_file'])
        save_results(results, results_file, format='json')

        # Save processed data
        output_file = Path(config['data']['output_file'])
        output_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_file, index=False)
        logger.info(f"Saved processed data to {output_file}")

        logger.info("\n" + "="*60)
        logger.info("ANALYSIS SUMMARY")
        logger.info("="*60)
        logger.info(f"\nH1 (Interception Rate):")
        logger.info(f"  Primary rate: {results['hypothesis_tests']['H1']['primary_rate']:.1%}")
        logger.info(f"  Help rate: {results['hypothesis_tests']['H1']['help_rate']:.1%}")
        logger.info(f"  p-value: {results['hypothesis_tests']['H1']['p_value_one_tailed']:.6f}")
        logger.info(f"  Significant: {results['hypothesis_tests']['H1']['significant']}")

        logger.info(f"\nH2 (Proximity):")
        logger.info(f"  Primary mean: {results['hypothesis_tests']['H2']['mean_primary']:.2f} yards")
        logger.info(f"  Help mean: {results['hypothesis_tests']['H2']['mean_help']:.2f} yards")
        logger.info(f"  Effect size: {results['hypothesis_tests']['H2']['effect_size']:.3f}")
        logger.info(f"  Significant: {results['hypothesis_tests']['H2']['significant']}")

        logger.info("\n" + "="*60)
        logger.info("Analysis complete!")

    except Exception as e:
        logger.error(f"Error during analysis: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
