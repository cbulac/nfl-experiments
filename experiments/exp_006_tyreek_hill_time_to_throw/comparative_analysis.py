#!/usr/bin/env python3
"""
Comparative Analysis: Top Receivers vs Tyreek Hill
Analyzes time-to-throw relationship for most targeted receiver from each team
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
import json
import glob
from scipy import stats

# Setup paths
exp_dir = Path(__file__).parent
project_root = exp_dir.parent.parent
data_dir = project_root / "data"
results_dir = exp_dir / "results"
figures_dir = results_dir / "figures"

# Create directories
results_dir.mkdir(exist_ok=True)
figures_dir.mkdir(exist_ok=True)

print("="*80)
print("COMPARATIVE ANALYSIS: Top Receivers vs Tyreek Hill")
print("="*80)

# Load top receivers list
print("\nLoading top receivers list...")
top_receivers_df = pd.read_csv(data_dir / "interim" / "top_receivers_by_team.csv")
print(f"Loaded {len(top_receivers_df)} top receivers")

# Load enhanced supplementary data
print("\nLoading supplementary data...")
supp_df = pd.read_csv(data_dir / "interim" / "supplementary_data_enhanced.csv", low_memory=False)
print(f"Loaded {len(supp_df):,} plays")

# Load tracking data for all top receivers
print("\nLoading tracking data for all top receivers...")
train_dir = data_dir / "raw" / "train"
input_files = sorted(glob.glob(str(train_dir / "input_2023_*.csv")))

target_receivers = top_receivers_df['player_name'].tolist()
print(f"Target receivers: {len(target_receivers)}")

all_receiver_data = []
for i, file_path in enumerate(input_files, 1):
    week = file_path.split('_')[-1].replace('.csv', '')
    print(f"  [{i}/{len(input_files)}] Processing week {week}...")

    for chunk in pd.read_csv(file_path, chunksize=100000):
        receiver_chunk = chunk[chunk['player_name'].isin(target_receivers)].copy()
        if len(receiver_chunk) > 0:
            all_receiver_data.append(receiver_chunk)

print("\nCombining tracking data...")
receivers_df = pd.concat(all_receiver_data, ignore_index=True)
print(f"Total frames: {len(receivers_df):,}")
print(f"Unique players: {receivers_df['player_name'].nunique()}")
print(f"Unique plays: {receivers_df.groupby(['game_id', 'play_id']).ngroups:,}")

# Calculate route metrics for each player-play
print("\nCalculating route metrics for each play...")

play_groups = receivers_df.groupby(['player_name', 'game_id', 'play_id'])
route_metrics = []

for (player_name, game_id, play_id), group in play_groups:
    group = group.sort_values('frame_id')

    # Calculate total distance
    x_diff = group['x'].diff()
    y_diff = group['y'].diff()
    distances = np.sqrt(x_diff**2 + y_diff**2)
    total_distance = distances.sum()

    # Start and end positions
    start_x, start_y = group.iloc[0][['x', 'y']]
    end_x, end_y = group.iloc[-1][['x', 'y']]

    # Displacement
    displacement = np.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)

    # Route efficiency
    route_efficiency = displacement / total_distance if total_distance > 0 else 0

    # Speed metrics
    max_speed = group['s'].max()
    avg_speed = group['s'].mean()

    # Max acceleration
    max_accel = group['a'].max()

    # Distance to ball
    ball_x = group.iloc[0]['ball_land_x']
    ball_y = group.iloc[0]['ball_land_y']
    final_dist_to_ball = np.sqrt((end_x - ball_x)**2 + (end_y - ball_y)**2)

    # Number of frames
    num_frames = len(group)

    route_metrics.append({
        'player_name': player_name,
        'game_id': game_id,
        'play_id': play_id,
        'total_distance': total_distance,
        'displacement': displacement,
        'route_efficiency': route_efficiency,
        'max_speed': max_speed,
        'avg_speed': avg_speed,
        'max_accel': max_accel,
        'final_dist_to_ball': final_dist_to_ball,
        'num_frames': num_frames
    })

route_df = pd.DataFrame(route_metrics)
print(f"Calculated metrics for {len(route_df):,} player-play combinations")

# Merge with supplementary data
print("\nMerging with supplementary data...")
full_analysis = route_df.merge(
    supp_df[['game_id', 'play_id', 'route_of_targeted_receiver', 'time_to_throw',
             'pass_result', 'yards_gained', 'pass_length', 'team_coverage_type',
             'possession_team']],
    on=['game_id', 'play_id'],
    how='left'
)

# Filter to targeted plays only
targeted_analysis = full_analysis[full_analysis['route_of_targeted_receiver'].notna()].copy()
print(f"Targeted plays: {len(targeted_analysis):,}")

# Filter to plays with time_to_throw
targeted_with_time = targeted_analysis[targeted_analysis['time_to_throw'].notna()].copy()
print(f"Targeted plays with time_to_throw: {len(targeted_with_time):,}")

# Add team info
targeted_with_time = targeted_with_time.merge(
    top_receivers_df[['player_name', 'possession_team', 'player_position', 'targets']],
    on='player_name',
    how='left',
    suffixes=('', '_total')
)

# Calculate per-player statistics
print("\n" + "="*80)
print("PER-PLAYER ANALYSIS")
print("="*80)

player_stats = targeted_with_time.groupby('player_name').agg({
    'play_id': 'count',
    'time_to_throw': ['mean', 'std'],
    'total_distance': ['mean', 'std'],
    'displacement': ['mean', 'std'],
    'route_efficiency': ['mean', 'std'],
    'max_speed': ['mean', 'max'],
    'final_dist_to_ball': ['mean', 'std'],
    'pass_result': lambda x: (x == 'C').sum()
}).round(2)

player_stats.columns = ['_'.join(col).strip('_') for col in player_stats.columns]
player_stats = player_stats.rename(columns={'play_id_count': 'plays_analyzed'})
player_stats['completion_pct'] = (player_stats['pass_result_<lambda>'] / player_stats['plays_analyzed'] * 100).round(1)

# Calculate correlation with time_to_throw for each player
print("\nCalculating correlations for each player...")
correlations = []
for player in targeted_with_time['player_name'].unique():
    player_data = targeted_with_time[targeted_with_time['player_name'] == player]
    if len(player_data) >= 10:  # Minimum 10 plays for correlation
        corr_distance = player_data[['time_to_throw', 'total_distance']].corr().iloc[0, 1]
        corr_efficiency = player_data[['time_to_throw', 'route_efficiency']].corr().iloc[0, 1]

        # Linear fit for distance vs time
        if player_data['time_to_throw'].std() > 0:
            slope, intercept = np.polyfit(player_data['time_to_throw'],
                                         player_data['total_distance'], 1)
        else:
            slope, intercept = 0, player_data['total_distance'].mean()

        correlations.append({
            'player_name': player,
            'corr_time_distance': corr_distance,
            'corr_time_efficiency': corr_efficiency,
            'yards_per_second': slope,
            'intercept': intercept
        })

corr_df = pd.DataFrame(correlations)
player_stats = player_stats.merge(corr_df, left_index=True, right_on='player_name', how='left')

# Add team info
player_stats = player_stats.merge(
    top_receivers_df[['player_name', 'possession_team', 'player_position']],
    on='player_name',
    how='left'
)

# Sort by yards per second (separation ability)
player_stats = player_stats.sort_values('yards_per_second', ascending=False)

print("\nTop 10 by Yards Per Second (Separation Ability):")
print(player_stats[['player_name', 'possession_team', 'yards_per_second', 'completion_pct',
                    'plays_analyzed']].head(10).to_string(index=False))

print("\nBottom 10 by Yards Per Second:")
print(player_stats[['player_name', 'possession_team', 'yards_per_second', 'completion_pct',
                    'plays_analyzed']].tail(10).to_string(index=False))

# Find Tyreek's rank
tyreek_rank = (player_stats['player_name'] == 'Tyreek Hill').idxmax()
tyreek_yps = player_stats.loc[player_stats['player_name'] == 'Tyreek Hill', 'yards_per_second'].values[0]
tyreek_position = (player_stats['yards_per_second'] > tyreek_yps).sum() + 1

print(f"\n{'='*80}")
print(f"TYREEK HILL RANKING")
print(f"{'='*80}")
print(f"Yards per second: {tyreek_yps:.2f}")
print(f"Rank: {tyreek_position} out of {len(player_stats)}")
print(f"Percentile: {(1 - tyreek_position/len(player_stats)) * 100:.1f}th")

# Save results
results = {
    'experiment': 'exp_006_comparative_analysis',
    'date': datetime.now().isoformat(),
    'total_receivers': len(player_stats),
    'total_plays_analyzed': int(targeted_with_time['play_id'].count()),
    'tyreek_hill': {
        'yards_per_second': float(tyreek_yps),
        'rank': int(tyreek_position),
        'percentile': float((1 - tyreek_position/len(player_stats)) * 100)
    },
    'player_stats': player_stats.to_dict(orient='records')
}

results_file = results_dir / "comparative_analysis.json"
with open(results_file, 'w') as f:
    json.dump(results, f, indent=2)
print(f"\n✓ Saved results to {results_file}")

# Create visualizations
print("\n" + "="*80)
print("CREATING VISUALIZATIONS")
print("="*80)

# 1. Distribution of yards per second
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('Top NFL Receivers: Route Metrics Comparison (2023)', fontsize=16, fontweight='bold')

# Yards per second distribution
ax = axes[0, 0]
player_stats_sorted = player_stats.sort_values('yards_per_second')
colors = ['red' if name == 'Tyreek Hill' else 'steelblue' for name in player_stats_sorted['player_name']]
ax.barh(range(len(player_stats_sorted)), player_stats_sorted['yards_per_second'], color=colors)
ax.set_yticks(range(len(player_stats_sorted)))
ax.set_yticklabels(player_stats_sorted['player_name'], fontsize=7)
ax.set_xlabel('Yards Per Second (Route Distance Gain)')
ax.set_title('Separation Ability: Distance Gained Per Second of Time to Throw')
ax.axvline(tyreek_yps, color='red', linestyle='--', linewidth=2, alpha=0.5, label='Tyreek Hill')
ax.grid(True, alpha=0.3, axis='x')
ax.legend()

# Completion % vs Yards Per Second
ax = axes[0, 1]
ax.scatter(player_stats['yards_per_second'], player_stats['completion_pct'], alpha=0.6, s=80)
# Highlight Tyreek
tyreek_row = player_stats[player_stats['player_name'] == 'Tyreek Hill']
ax.scatter(tyreek_row['yards_per_second'], tyreek_row['completion_pct'],
           color='red', s=200, marker='*', label='Tyreek Hill', edgecolors='black', linewidth=2)
ax.set_xlabel('Yards Per Second')
ax.set_ylabel('Completion %')
ax.set_title('Completion % vs Separation Ability')
ax.grid(True, alpha=0.3)
ax.legend()

# Add correlation
corr = player_stats[['yards_per_second', 'completion_pct']].corr().iloc[0, 1]
ax.text(0.05, 0.95, f'Correlation: {corr:.3f}', transform=ax.transAxes,
        fontsize=10, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Route efficiency distribution
ax = axes[1, 0]
player_stats_eff = player_stats.sort_values('route_efficiency_mean')
colors_eff = ['red' if name == 'Tyreek Hill' else 'seagreen' for name in player_stats_eff['player_name']]
ax.barh(range(len(player_stats_eff)), player_stats_eff['route_efficiency_mean'], color=colors_eff)
ax.set_yticks(range(len(player_stats_eff)))
ax.set_yticklabels(player_stats_eff['player_name'], fontsize=7)
ax.set_xlabel('Average Route Efficiency')
ax.set_title('Route Precision: Efficiency (Displacement/Distance)')
tyreek_eff = tyreek_row['route_efficiency_mean'].values[0]
ax.axvline(tyreek_eff, color='red', linestyle='--', linewidth=2, alpha=0.5, label='Tyreek Hill')
ax.grid(True, alpha=0.3, axis='x')
ax.legend()

# Max speed distribution
ax = axes[1, 1]
player_stats_speed = player_stats.sort_values('max_speed_mean')
colors_speed = ['red' if name == 'Tyreek Hill' else 'coral' for name in player_stats_speed['player_name']]
ax.barh(range(len(player_stats_speed)), player_stats_speed['max_speed_mean'], color=colors_speed)
ax.set_yticks(range(len(player_stats_speed)))
ax.set_yticklabels(player_stats_speed['player_name'], fontsize=7)
ax.set_xlabel('Average Max Speed (mph)')
ax.set_title('Speed: Average Maximum Speed Reached on Routes')
tyreek_speed = tyreek_row['max_speed_mean'].values[0]
ax.axvline(tyreek_speed, color='red', linestyle='--', linewidth=2, alpha=0.5, label='Tyreek Hill')
ax.grid(True, alpha=0.3, axis='x')
ax.legend()

plt.tight_layout()
fig_path = figures_dir / "comparative_metrics.png"
plt.savefig(fig_path, dpi=300, bbox_inches='tight')
print(f"✓ Saved {fig_path}")
plt.close()

# 2. Time to throw curves for top receivers
fig, ax = plt.subplots(figsize=(14, 8))
fig.suptitle('Route Distance vs Time to Throw: Top 10 Separation Leaders', fontsize=14, fontweight='bold')

top_10_separation = player_stats.nlargest(10, 'yards_per_second')

for _, player in top_10_separation.iterrows():
    player_data = targeted_with_time[targeted_with_time['player_name'] == player['player_name']]

    if len(player_data) >= 10:
        # Plot scatter
        if player['player_name'] == 'Tyreek Hill':
            ax.scatter(player_data['time_to_throw'], player_data['total_distance'],
                      alpha=0.3, s=20, color='red', label=f"{player['player_name']} ({player['possession_team']})")
            # Plot trend line
            x_range = np.linspace(player_data['time_to_throw'].min(),
                                 player_data['time_to_throw'].max(), 100)
            y_pred = player['yards_per_second'] * x_range + player['intercept']
            ax.plot(x_range, y_pred, linewidth=3, color='red', linestyle='-')
        else:
            ax.scatter(player_data['time_to_throw'], player_data['total_distance'],
                      alpha=0.2, s=15, label=f"{player['player_name']} ({player['possession_team']})")
            # Plot trend line
            x_range = np.linspace(player_data['time_to_throw'].min(),
                                 player_data['time_to_throw'].max(), 100)
            y_pred = player['yards_per_second'] * x_range + player['intercept']
            ax.plot(x_range, y_pred, linewidth=2, alpha=0.7)

ax.set_xlabel('Time to Throw (seconds)', fontsize=12)
ax.set_ylabel('Total Route Distance (yards)', fontsize=12)
ax.set_title('Steeper slope = Better separation ability', fontsize=10, style='italic')
ax.grid(True, alpha=0.3)
ax.legend(loc='upper left', fontsize=8, ncol=2)

plt.tight_layout()
fig_path = figures_dir / "top_10_separation_curves.png"
plt.savefig(fig_path, dpi=300, bbox_inches='tight')
print(f"✓ Saved {fig_path}")
plt.close()

# Save player stats to CSV
player_stats_file = results_dir / "player_comparison_stats.csv"
player_stats.to_csv(player_stats_file, index=False)
print(f"✓ Saved player stats to {player_stats_file}")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
print(f"\nResults saved to: {results_dir}")
print(f"Figures saved to: {figures_dir}")
