"""
Experiment 005: DaRon Bland Interception Analysis

Focus: Analyze DaRon Bland's positioning, angles, and separation at throw time
       compared to other cornerbacks on interception plays.

Research Questions:
1. How does Bland position himself differently on INT plays?
2. What are his angles to the ball vs. other CBs?
3. What is his separation from the receiver at throw moment?
4. Are there patterns in how he reads and reacts to plays?
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import logging
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Setup paths
script_dir = Path(__file__).parent
project_root = script_dir.parents[1]
data_dir = project_root / "data"
results_dir = script_dir / "results"
figures_dir = results_dir / "figures"
logs_dir = script_dir / "logs"

# Create directories
results_dir.mkdir(exist_ok=True)
figures_dir.mkdir(exist_ok=True)
logs_dir.mkdir(exist_ok=True)

# Setup logging
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file = logs_dir / f"{timestamp}_run.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_tracking_data():
    """Load frame-level tracking data for detailed analysis."""
    logger.info("Loading merged tracking data...")

    tracking_path = data_dir / "interim" / "merged_tracking_data.csv"

    # Load relevant columns
    cols = [
        'game_id', 'play_id', 'nfl_id', 'frame_id', 'player_name',
        'player_position', 'x', 'y', 's', 'a', 'dir', 'o',
        'ball_land_x', 'ball_land_y', 'player_to_predict',
        'week_x', 'season', 'play_description', 'pass_result',
        'team_coverage_man_zone', 'team_coverage_type',
        'num_frames_output', 'position_group'
    ]

    df = pd.read_csv(tracking_path, usecols=cols)

    # Filter to only cornerbacks
    df = df[df['player_position'] == 'CB'].copy()

    logger.info(f"Loaded {len(df)} CB frame observations")
    logger.info(f"Unique CBs: {df['player_name'].nunique()}")

    return df


def identify_interception_plays(df):
    """Identify plays that resulted in interceptions."""
    logger.info("Identifying interception plays...")

    # Filter to only interception plays
    int_df = df[df['player_to_predict'] == True].copy()

    logger.info(f"Found {int_df['play_id'].nunique()} interception plays")
    logger.info(f"Total INT observations (all frames): {len(int_df)}")

    # Get unique intercepting players
    int_players = int_df.groupby('player_name')['play_id'].nunique().sort_values(ascending=False)
    logger.info(f"\nTop 10 CBs by interceptions:")
    logger.info(int_players.head(10))

    return int_df, int_players


def calculate_throw_moment_metrics(df):
    """Calculate positioning metrics at the moment of the throw."""
    logger.info("Calculating throw moment metrics...")

    # For each play, get the LAST frame (throw moment)
    throw_frame = df.sort_values('frame_id').groupby(['game_id', 'play_id', 'nfl_id']).last().reset_index()

    # Calculate distance to ball landing location
    throw_frame['dist_to_ball'] = np.sqrt(
        (throw_frame['x'] - throw_frame['ball_land_x'])**2 +
        (throw_frame['y'] - throw_frame['ball_land_y'])**2
    )

    # Calculate angle to ball (direction relative to ball landing location)
    # This shows if CB is positioned between QB and ball landing spot
    dx = throw_frame['ball_land_x'] - throw_frame['x']
    dy = throw_frame['ball_land_y'] - throw_frame['y']
    throw_frame['angle_to_ball'] = np.degrees(np.arctan2(dy, dx))

    # Calculate closure angle (how oriented toward ball is the player)
    # Difference between player's orientation and angle to ball
    throw_frame['closure_angle'] = np.abs(throw_frame['o'] - throw_frame['angle_to_ball'])
    # Normalize to 0-180 degrees
    throw_frame['closure_angle'] = throw_frame['closure_angle'].apply(
        lambda x: min(x, 360 - x) if x > 180 else x
    )

    # Calculate pursuit angle (how oriented toward ball is player's movement direction)
    throw_frame['pursuit_angle'] = np.abs(throw_frame['dir'] - throw_frame['angle_to_ball'])
    throw_frame['pursuit_angle'] = throw_frame['pursuit_angle'].apply(
        lambda x: min(x, 360 - x) if x > 180 else x
    )

    logger.info(f"Calculated metrics for {len(throw_frame)} player-play observations")

    return throw_frame


def calculate_first_frame_metrics(df):
    """Calculate positioning metrics at play start for comparison."""
    logger.info("Calculating first frame metrics...")

    first_frame = df.sort_values('frame_id').groupby(['game_id', 'play_id', 'nfl_id']).first().reset_index()

    first_frame['initial_dist_to_ball'] = np.sqrt(
        (first_frame['x'] - first_frame['ball_land_x'])**2 +
        (first_frame['y'] - first_frame['ball_land_y'])**2
    )

    logger.info(f"Calculated initial metrics for {len(first_frame)} player-play observations")

    return first_frame[['game_id', 'play_id', 'nfl_id', 'initial_dist_to_ball']]


def analyze_bland_vs_others(throw_metrics):
    """Compare DaRon Bland's metrics to other CBs."""
    logger.info("\n" + "="*60)
    logger.info("DARON BLAND ANALYSIS")
    logger.info("="*60)

    # Separate Bland from others
    bland_df = throw_metrics[throw_metrics['player_name'] == 'DaRon Bland'].copy()
    others_df = throw_metrics[throw_metrics['player_name'] != 'DaRon Bland'].copy()

    logger.info(f"\nDaRon Bland INT plays: {len(bland_df)}")
    logger.info(f"Other CBs INT plays: {len(others_df)}")

    # Statistical comparison
    metrics_to_compare = [
        ('dist_to_ball', 'Distance to Ball (yards)'),
        ('s', 'Speed at Throw (mph)'),
        ('a', 'Acceleration at Throw (mph/s)'),
        ('closure_angle', 'Closure Angle (degrees)'),
        ('pursuit_angle', 'Pursuit Angle (degrees)'),
    ]

    results = {}

    for metric, label in metrics_to_compare:
        bland_vals = bland_df[metric].dropna()
        other_vals = others_df[metric].dropna()

        bland_mean = bland_vals.mean()
        bland_std = bland_vals.std()
        other_mean = other_vals.mean()
        other_std = other_vals.std()

        # T-test
        t_stat, p_val = stats.ttest_ind(bland_vals, other_vals, equal_var=False)

        # Effect size (Cohen's d)
        pooled_std = np.sqrt((bland_std**2 + other_std**2) / 2)
        cohens_d = (bland_mean - other_mean) / pooled_std if pooled_std > 0 else 0

        results[metric] = {
            'bland_mean': bland_mean,
            'bland_std': bland_std,
            'bland_n': len(bland_vals),
            'other_mean': other_mean,
            'other_std': other_std,
            'other_n': len(other_vals),
            'difference': bland_mean - other_mean,
            't_statistic': t_stat,
            'p_value': p_val,
            'cohens_d': cohens_d,
            'significant': p_val < 0.05
        }

        logger.info(f"\n{label}:")
        logger.info(f"  Bland: {bland_mean:.2f} ± {bland_std:.2f} (n={len(bland_vals)})")
        logger.info(f"  Others: {other_mean:.2f} ± {other_std:.2f} (n={len(other_vals)})")
        logger.info(f"  Difference: {bland_mean - other_mean:.2f}")
        logger.info(f"  Effect size (d): {cohens_d:.3f}")
        logger.info(f"  p-value: {p_val:.6f} {'***' if p_val < 0.001 else '**' if p_val < 0.01 else '*' if p_val < 0.05 else 'ns'}")

    return results, bland_df, others_df


def analyze_coverage_types(throw_metrics):
    """Analyze Bland's performance across different coverage types."""
    logger.info("\n" + "="*60)
    logger.info("COVERAGE TYPE ANALYSIS")
    logger.info("="*60)

    bland_df = throw_metrics[throw_metrics['player_name'] == 'DaRon Bland'].copy()

    # Group by coverage type
    coverage_summary = bland_df.groupby('team_coverage_type').agg({
        'play_id': 'count',
        'dist_to_ball': 'mean',
        'closure_angle': 'mean',
        'pursuit_angle': 'mean',
        's': 'mean'
    }).round(2)

    coverage_summary.columns = ['INT_Count', 'Avg_Dist', 'Avg_Closure_Angle', 'Avg_Pursuit_Angle', 'Avg_Speed']
    coverage_summary = coverage_summary.sort_values('INT_Count', ascending=False)

    logger.info("\nBland's INTs by Coverage Type:")
    logger.info(coverage_summary)

    return coverage_summary


def visualize_bland_comparison(results, bland_df, others_df, figures_dir):
    """Create visualizations comparing Bland to other CBs."""
    logger.info("\nGenerating visualizations...")

    # Set style
    sns.set_style("whitegrid")
    plt.rcParams['figure.figsize'] = (15, 10)

    # Create 2x3 subplot
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle("DaRon Bland vs. Other Cornerbacks - Interception Analysis",
                 fontsize=16, fontweight='bold', y=0.995)

    metrics = [
        ('dist_to_ball', 'Distance to Ball at Throw (yards)', 0, 0),
        ('s', 'Speed at Throw Moment (mph)', 0, 1),
        ('a', 'Acceleration at Throw (mph/s)', 0, 2),
        ('closure_angle', 'Closure Angle (degrees)', 1, 0),
        ('pursuit_angle', 'Pursuit Angle (degrees)', 1, 1),
    ]

    for metric, title, row, col in metrics:
        ax = axes[row, col]

        # Prepare data
        bland_vals = bland_df[metric].dropna()
        other_vals = others_df[metric].dropna()

        data_to_plot = [bland_vals, other_vals]
        labels = [f'DaRon Bland\n(n={len(bland_vals)})', f'Other CBs\n(n={len(other_vals)})']

        # Box plot
        bp = ax.boxplot(data_to_plot, labels=labels, patch_artist=True,
                        showmeans=True, meanline=True)

        # Color boxes
        colors = ['#0d3b66', '#f95738']  # Bland in blue, others in red
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.6)

        # Add mean values as text
        bland_mean = bland_vals.mean()
        other_mean = other_vals.mean()
        ax.text(1, bland_mean, f'{bland_mean:.2f}', ha='center', va='bottom', fontweight='bold')
        ax.text(2, other_mean, f'{other_mean:.2f}', ha='center', va='bottom', fontweight='bold')

        # Add significance stars
        p_val = results[metric]['p_value']
        if p_val < 0.001:
            sig_text = '***'
        elif p_val < 0.01:
            sig_text = '**'
        elif p_val < 0.05:
            sig_text = '*'
        else:
            sig_text = 'ns'

        y_max = max(bland_vals.max(), other_vals.max())
        ax.text(1.5, y_max * 1.05, sig_text, ha='center', fontsize=14, fontweight='bold')

        ax.set_title(title, fontweight='bold')
        ax.set_ylabel('Value')
        ax.grid(True, alpha=0.3)

    # Remove the empty 6th subplot
    fig.delaxes(axes[1, 2])

    # Add summary text in the empty space
    summary_ax = fig.add_subplot(2, 3, 6)
    summary_ax.axis('off')

    summary_text = "KEY FINDINGS:\n\n"
    summary_text += f"• Bland INTs: {len(bland_df)}\n"
    summary_text += f"• Other CBs INTs: {len(others_df)}\n\n"

    # Identify significant differences
    sig_metrics = [m for m in metrics if results[m[0]]['significant']]
    if sig_metrics:
        summary_text += "Significant Differences (p < 0.05):\n"
        for metric, label, _, _ in sig_metrics:
            diff = results[metric]['difference']
            d = results[metric]['cohens_d']
            summary_text += f"• {label.split('(')[0].strip()}: "
            summary_text += f"{'+' if diff > 0 else ''}{diff:.2f} (d={d:.2f})\n"

    summary_ax.text(0.1, 0.5, summary_text, fontsize=11, family='monospace',
                    verticalalignment='center', bbox=dict(boxstyle='round',
                    facecolor='wheat', alpha=0.3))

    plt.tight_layout()
    output_path = figures_dir / "bland_vs_others_comparison.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    logger.info(f"Saved: {output_path}")
    plt.close()

    # Create scatter plot: Distance vs Angles
    fig, ax = plt.subplots(figsize=(12, 8))

    ax.scatter(others_df['dist_to_ball'], others_df['closure_angle'],
               alpha=0.5, s=50, c='#f95738', label=f'Other CBs (n={len(others_df)})')
    ax.scatter(bland_df['dist_to_ball'], bland_df['closure_angle'],
               alpha=0.8, s=100, c='#0d3b66', marker='*',
               label=f'DaRon Bland (n={len(bland_df)})', edgecolors='black', linewidths=1)

    ax.set_xlabel('Distance to Ball at Throw (yards)', fontweight='bold', fontsize=12)
    ax.set_ylabel('Closure Angle (degrees)', fontweight='bold', fontsize=12)
    ax.set_title('Ball Distance vs. Closure Angle at Throw Moment',
                 fontweight='bold', fontsize=14)
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)

    output_path = figures_dir / "bland_positioning_scatter.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    logger.info(f"Saved: {output_path}")
    plt.close()


def analyze_play_details(bland_df):
    """Analyze specific plays where Bland intercepted the ball."""
    logger.info("\n" + "="*60)
    logger.info("BLAND'S INDIVIDUAL INTERCEPTION PLAYS")
    logger.info("="*60)

    # Get play-level details
    play_summary = bland_df.groupby(['game_id', 'play_id']).agg({
        'week_x': 'first',
        'season': 'first',
        'play_description': 'first',
        'dist_to_ball': 'first',
        'closure_angle': 'first',
        'pursuit_angle': 'first',
        's': 'first',
        'team_coverage_type': 'first'
    }).reset_index()

    play_summary = play_summary.sort_values('dist_to_ball')

    logger.info(f"\nAll {len(play_summary)} DaRon Bland INT plays:")
    for idx, row in play_summary.iterrows():
        logger.info(f"\n--- Play {idx + 1} ---")
        logger.info(f"Week {row['week_x']}, {row['season']}")
        logger.info(f"Coverage: {row['team_coverage_type']}")
        logger.info(f"Distance to ball: {row['dist_to_ball']:.2f} yards")
        logger.info(f"Closure angle: {row['closure_angle']:.2f}°")
        logger.info(f"Pursuit angle: {row['pursuit_angle']:.2f}°")
        logger.info(f"Speed at throw: {row['s']:.2f} mph")
        logger.info(f"Description: {row['play_description'][:100]}...")

    return play_summary


def main():
    """Main analysis pipeline."""
    logger.info("="*60)
    logger.info("EXPERIMENT 005: DaRon Bland Interception Analysis")
    logger.info("="*60)

    # Load data
    tracking_df = load_tracking_data()

    # Identify interceptions
    int_df, int_players = identify_interception_plays(tracking_df)

    # Check if Bland is in the data
    if 'DaRon Bland' not in int_players.index:
        logger.error("DaRon Bland not found in interception data!")
        return

    bland_int_count = int_players['DaRon Bland']
    logger.info(f"\nDaRon Bland interceptions in dataset: {bland_int_count}")

    # Calculate metrics at throw moment
    throw_metrics = calculate_throw_moment_metrics(int_df)

    # Merge with first frame metrics
    first_frame = calculate_first_frame_metrics(int_df)
    throw_metrics = throw_metrics.merge(first_frame, on=['game_id', 'play_id', 'nfl_id'], how='left')

    # Calculate positional change
    throw_metrics['distance_closed'] = throw_metrics['initial_dist_to_ball'] - throw_metrics['dist_to_ball']

    # Analyze Bland vs others
    comparison_results, bland_df, others_df = analyze_bland_vs_others(throw_metrics)

    # Analyze coverage types
    coverage_summary = analyze_coverage_types(throw_metrics)

    # Analyze individual plays
    play_details = analyze_play_details(bland_df)

    # Generate visualizations
    visualize_bland_comparison(comparison_results, bland_df, others_df, figures_dir)

    # Save results
    output = {
        'experiment': 'exp_005_daron_bland_analysis',
        'date': datetime.now().isoformat(),
        'bland_interceptions': int(bland_int_count),
        'total_cb_interceptions': int(int_players.sum()),
        'comparison_metrics': {
            k: {key: (float(val) if isinstance(val, (np.integer, np.floating))
                     else bool(val) if isinstance(val, (bool, np.bool_))
                     else val)
                for key, val in v.items()}
            for k, v in comparison_results.items()
        },
        'coverage_analysis': coverage_summary.to_dict()
    }

    output_path = results_dir / "bland_analysis.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    logger.info(f"\nSaved results to: {output_path}")

    logger.info("\n" + "="*60)
    logger.info("ANALYSIS COMPLETE")
    logger.info("="*60)


if __name__ == "__main__":
    main()
