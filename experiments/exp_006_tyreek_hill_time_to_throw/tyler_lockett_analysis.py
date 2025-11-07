#!/usr/bin/env python3
"""
Tyler Lockett Analysis: Precision Route Runner vs Speed Separator

Analyzes Tyler Lockett's route running to contrast with Tyreek Hill's style.
Lockett ranks #32/32 in separation ability but #3/32 in completion %.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
import json
import glob

# Setup paths
exp_dir = Path(__file__).parent
project_root = exp_dir.parent.parent
data_dir = project_root / "data"
results_dir = exp_dir / "results"
figures_dir = results_dir / "figures"
logs_dir = exp_dir / "logs"

# Create directories
results_dir.mkdir(exist_ok=True)
figures_dir.mkdir(exist_ok=True)
logs_dir.mkdir(exist_ok=True)

# Setup logging
log_file = logs_dir / f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_lockett_run.log"

def log(message):
    """Log message to both console and file"""
    print(message)
    with open(log_file, 'a') as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

log("="*80)
log("Tyler Lockett Analysis: Precision vs Speed")
log("="*80)

# Load enhanced supplementary data
log("\nLoading enhanced supplementary data...")
supp_path = data_dir / "interim" / "supplementary_data_enhanced.csv"
supp_df = pd.read_csv(supp_path, low_memory=False)

# Load tracking data for Tyler Lockett
log("\nLoading Tyler Lockett tracking data...")
train_dir = data_dir / "raw" / "train"
input_files = sorted(glob.glob(str(train_dir / "input_2023_*.csv")))

lockett_data = []
for i, file_path in enumerate(input_files, 1):
    week = file_path.split('_')[-1].replace('.csv', '')
    log(f"  [{i}/{len(input_files)}] Processing week {week}...")

    for chunk in pd.read_csv(file_path, chunksize=100000):
        lockett_chunk = chunk[chunk['player_name'] == 'Tyler Lockett'].copy()
        if len(lockett_chunk) > 0:
            lockett_data.append(lockett_chunk)

log("\nCombining Tyler Lockett data...")
lockett_df = pd.concat(lockett_data, ignore_index=True)
log(f"Total Lockett frames: {len(lockett_df):,}")
log(f"Unique plays: {lockett_df['play_id'].nunique():,}")

# Calculate route metrics
log("\nCalculating route metrics...")

play_groups = lockett_df.groupby(['game_id', 'play_id'])
route_metrics = []

for (game_id, play_id), group in play_groups:
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
    max_accel = group['a'].max()

    # Distance to ball
    ball_x = group.iloc[0]['ball_land_x']
    ball_y = group.iloc[0]['ball_land_y']
    final_dist_to_ball = np.sqrt((end_x - ball_x)**2 + (end_y - ball_y)**2)

    num_frames = len(group)

    route_metrics.append({
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
log(f"Calculated metrics for {len(route_df):,} plays")

# Merge with supplementary data
log("\nMerging with supplementary data...")
lockett_analysis = route_df.merge(
    supp_df[['game_id', 'play_id', 'route_of_targeted_receiver', 'time_to_throw',
             'pass_result', 'yards_gained', 'pass_length', 'team_coverage_type',
             'play_description']],
    on=['game_id', 'play_id'],
    how='left'
)

# Filter to targeted plays
lockett_targeted = lockett_analysis[lockett_analysis['route_of_targeted_receiver'].notna()].copy()
log(f"Plays where Lockett was targeted: {len(lockett_targeted):,}")

# Filter to plays with time_to_throw
lockett_with_time = lockett_targeted[lockett_targeted['time_to_throw'].notna()].copy()
log(f"Targeted plays with time_to_throw: {len(lockett_with_time):,}")

# Route analysis
log("\n" + "="*80)
log("ROUTE TYPE ANALYSIS")
log("="*80)

route_summary = lockett_with_time.groupby('route_of_targeted_receiver').agg({
    'play_id': 'count',
    'time_to_throw': ['mean', 'std'],
    'route_efficiency': ['mean', 'std'],
    'total_distance': ['mean', 'std'],
    'displacement': ['mean', 'std'],
    'max_speed': ['mean', 'max'],
    'final_dist_to_ball': ['mean', 'std'],
    'pass_result': lambda x: (x == 'C').sum(),
}).round(2)

route_summary.columns = ['_'.join(col).strip('_') for col in route_summary.columns]
route_summary = route_summary.rename(columns={'play_id_count': 'targets'})
route_summary['completion_pct'] = (route_summary['pass_result_<lambda>'] / route_summary['targets'] * 100).round(1)
route_summary = route_summary.sort_values('targets', ascending=False)

log("\nRoute Type Summary:")
log(route_summary.to_string())

# Time bins analysis
log("\n" + "="*80)
log("TIME TO THROW BINS")
log("="*80)

bins = [0, 2.0, 2.5, 3.0, 3.5, 15]
labels = ['Quick (<2s)', 'Fast (2-2.5s)', 'Normal (2.5-3s)', 'Slow (3-3.5s)', 'Very Slow (>3.5s)']
lockett_with_time['time_bin'] = pd.cut(lockett_with_time['time_to_throw'], bins=bins, labels=labels)

time_bin_summary = lockett_with_time.groupby('time_bin').agg({
    'play_id': 'count',
    'route_efficiency': 'mean',
    'total_distance': 'mean',
    'displacement': 'mean',
    'max_speed': 'mean',
    'final_dist_to_ball': 'mean',
    'pass_result': lambda x: (x == 'C').sum(),
}).round(2)

time_bin_summary.columns = ['targets', 'avg_route_efficiency', 'avg_total_distance',
                            'avg_displacement', 'avg_max_speed', 'avg_final_dist_to_ball',
                            'completions']
time_bin_summary['completion_pct'] = (time_bin_summary['completions'] / time_bin_summary['targets'] * 100).round(1)

log("\nTime Bin Summary:")
log(time_bin_summary.to_string())

# Correlations
log("\n" + "="*80)
log("CORRELATIONS")
log("="*80)

correlations = lockett_with_time[['time_to_throw', 'route_efficiency', 'total_distance',
                                   'displacement', 'max_speed', 'final_dist_to_ball']].corr()['time_to_throw'].sort_values(ascending=False)
log("\nCorrelations with time_to_throw:")
log(correlations.to_string())

# Load Tyreek data for comparison
log("\n" + "="*80)
log("LOADING TYREEK HILL DATA FOR COMPARISON")
log("="*80)

tyreek_data = []
for i, file_path in enumerate(input_files, 1):
    week = file_path.split('_')[-1].replace('.csv', '')
    log(f"  [{i}/{len(input_files)}] Processing week {week}...")

    for chunk in pd.read_csv(file_path, chunksize=100000):
        tyreek_chunk = chunk[chunk['player_name'] == 'Tyreek Hill'].copy()
        if len(tyreek_chunk) > 0:
            tyreek_data.append(tyreek_chunk)

log("\nCombining Tyreek Hill data...")
tyreek_df = pd.concat(tyreek_data, ignore_index=True)

# Calculate Tyreek metrics
log("\nCalculating Tyreek metrics...")
tyreek_play_groups = tyreek_df.groupby(['game_id', 'play_id'])
tyreek_route_metrics = []

for (game_id, play_id), group in tyreek_play_groups:
    group = group.sort_values('frame_id')

    x_diff = group['x'].diff()
    y_diff = group['y'].diff()
    distances = np.sqrt(x_diff**2 + y_diff**2)
    total_distance = distances.sum()

    start_x, start_y = group.iloc[0][['x', 'y']]
    end_x, end_y = group.iloc[-1][['x', 'y']]
    displacement = np.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
    route_efficiency = displacement / total_distance if total_distance > 0 else 0
    max_speed = group['s'].max()
    avg_speed = group['s'].mean()

    ball_x = group.iloc[0]['ball_land_x']
    ball_y = group.iloc[0]['ball_land_y']
    final_dist_to_ball = np.sqrt((end_x - ball_x)**2 + (end_y - ball_y)**2)

    tyreek_route_metrics.append({
        'game_id': game_id,
        'play_id': play_id,
        'total_distance': total_distance,
        'displacement': displacement,
        'route_efficiency': route_efficiency,
        'max_speed': max_speed,
        'avg_speed': avg_speed,
        'final_dist_to_ball': final_dist_to_ball,
    })

tyreek_route_df = pd.DataFrame(tyreek_route_metrics)

# Merge Tyreek with supp data
tyreek_analysis = tyreek_route_df.merge(
    supp_df[['game_id', 'play_id', 'route_of_targeted_receiver', 'time_to_throw', 'pass_result']],
    on=['game_id', 'play_id'],
    how='left'
)

tyreek_targeted = tyreek_analysis[
    (tyreek_analysis['route_of_targeted_receiver'].notna()) &
    (tyreek_analysis['time_to_throw'].notna())
].copy()

log(f"Tyreek targeted plays with time data: {len(tyreek_targeted):,}")

# Save results
results = {
    'experiment': 'tyler_lockett_analysis',
    'date': datetime.now().isoformat(),
    'player': 'Tyler Lockett',
    'team': 'SEA',
    'total_plays': len(lockett_with_time),
    'overall_stats': {
        'avg_time_to_throw': float(lockett_with_time['time_to_throw'].mean()),
        'avg_route_efficiency': float(lockett_with_time['route_efficiency'].mean()),
        'avg_total_distance': float(lockett_with_time['total_distance'].mean()),
        'avg_max_speed': float(lockett_with_time['max_speed'].mean()),
        'overall_completion_pct': float((lockett_with_time['pass_result'] == 'C').sum() / len(lockett_with_time) * 100),
        'yards_per_second': float(np.polyfit(lockett_with_time['time_to_throw'], lockett_with_time['total_distance'], 1)[0])
    },
    'route_summary': route_summary.to_dict(),
    'time_bin_summary': time_bin_summary.to_dict(),
    'correlations': correlations.to_dict()
}

results_file = results_dir / "tyler_lockett_analysis.json"
with open(results_file, 'w') as f:
    json.dump(results, f, indent=2)
log(f"\n✓ Saved results to {results_file}")

# Create visualizations
log("\n" + "="*80)
log("CREATING VISUALIZATIONS")
log("="*80)

# 1. Side-by-side comparison: Lockett vs Tyreek
fig, axes = plt.subplots(2, 3, figsize=(18, 12))
fig.suptitle('Tyler Lockett vs Tyreek Hill: Contrasting Styles', fontsize=16, fontweight='bold')

# Plot 1: Route Distance vs Time (both players)
ax = axes[0, 0]
ax.scatter(lockett_with_time['time_to_throw'], lockett_with_time['total_distance'],
           alpha=0.4, s=30, color='blue', label='Tyler Lockett')
ax.scatter(tyreek_targeted['time_to_throw'], tyreek_targeted['total_distance'],
           alpha=0.4, s=30, color='red', label='Tyreek Hill')

# Trend lines
z_lockett = np.polyfit(lockett_with_time['time_to_throw'], lockett_with_time['total_distance'], 1)
z_tyreek = np.polyfit(tyreek_targeted['time_to_throw'], tyreek_targeted['total_distance'], 1)
p_lockett = np.poly1d(z_lockett)
p_tyreek = np.poly1d(z_tyreek)

x_range = np.linspace(1, 6, 100)
ax.plot(x_range, p_lockett(x_range), 'b--', linewidth=2, label=f'Lockett: {z_lockett[0]:.2f} yds/sec')
ax.plot(x_range, p_tyreek(x_range), 'r--', linewidth=2, label=f'Tyreek: {z_tyreek[0]:.2f} yds/sec')

ax.set_xlabel('Time to Throw (seconds)')
ax.set_ylabel('Total Route Distance (yards)')
ax.set_title('Separation Ability: Distance vs Time')
ax.legend()
ax.grid(True, alpha=0.3)

# Plot 2: Route Efficiency Comparison
ax = axes[0, 1]
ax.scatter(lockett_with_time['time_to_throw'], lockett_with_time['route_efficiency'],
           alpha=0.4, s=30, color='blue', label='Tyler Lockett')
ax.scatter(tyreek_targeted['time_to_throw'], tyreek_targeted['route_efficiency'],
           alpha=0.4, s=30, color='red', label='Tyreek Hill')
ax.set_xlabel('Time to Throw (seconds)')
ax.set_ylabel('Route Efficiency')
ax.set_title('Route Precision: Efficiency Over Time')
ax.legend()
ax.grid(True, alpha=0.3)

# Add mean lines
ax.axhline(lockett_with_time['route_efficiency'].mean(), color='blue', linestyle=':', linewidth=2, alpha=0.7)
ax.axhline(tyreek_targeted['route_efficiency'].mean(), color='red', linestyle=':', linewidth=2, alpha=0.7)

# Plot 3: Max Speed Comparison
ax = axes[0, 2]
ax.scatter(lockett_with_time['time_to_throw'], lockett_with_time['max_speed'],
           alpha=0.4, s=30, color='blue', label='Tyler Lockett')
ax.scatter(tyreek_targeted['time_to_throw'], tyreek_targeted['max_speed'],
           alpha=0.4, s=30, color='red', label='Tyreek Hill')
ax.set_xlabel('Time to Throw (seconds)')
ax.set_ylabel('Max Speed (mph)')
ax.set_title('Speed Comparison')
ax.legend()
ax.grid(True, alpha=0.3)

# Plot 4: Lockett Completion % by Time Bin
ax = axes[1, 0]
time_bin_summary.reset_index()[['time_bin', 'completion_pct']].plot(
    kind='bar', x='time_bin', y='completion_pct', ax=ax, legend=False, color='steelblue'
)
ax.set_xlabel('Time to Throw Bin')
ax.set_ylabel('Completion %')
ax.set_title('Lockett: Completion % by Time')
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
ax.grid(True, alpha=0.3, axis='y')
ax.axhline(72.2, color='green', linestyle='--', linewidth=2, label='Overall: 72.2%')
ax.legend()

# Plot 5: Route Type Comparison (Top 8 for Lockett)
ax = axes[1, 1]
top_routes = route_summary.nlargest(8, 'targets')
top_routes['targets'].plot(kind='barh', ax=ax, color='cornflowerblue')
ax.set_xlabel('Targets')
ax.set_ylabel('Route Type')
ax.set_title('Lockett: Most Frequent Routes')
ax.grid(True, alpha=0.3, axis='x')

# Plot 6: Completion % by Route Type
ax = axes[1, 2]
top_routes['completion_pct'].plot(kind='barh', ax=ax, color='mediumseagreen')
ax.set_xlabel('Completion %')
ax.set_ylabel('Route Type')
ax.set_title('Lockett: Completion % by Route')
ax.grid(True, alpha=0.3, axis='x')

plt.tight_layout()
fig_path = figures_dir / "lockett_vs_tyreek_analysis.png"
plt.savefig(fig_path, dpi=300, bbox_inches='tight')
log(f"✓ Saved {fig_path}")
plt.close()

# 2. Lockett-specific deep dive
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Tyler Lockett: Precision Route Runner Profile', fontsize=14, fontweight='bold')

# Distribution of route distances
ax = axes[0, 0]
ax.hist(lockett_with_time['total_distance'], bins=30, color='steelblue', alpha=0.7, edgecolor='black')
ax.axvline(lockett_with_time['total_distance'].mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {lockett_with_time["total_distance"].mean():.1f} yds')
ax.set_xlabel('Total Route Distance (yards)')
ax.set_ylabel('Frequency')
ax.set_title('Distribution of Route Distances')
ax.legend()
ax.grid(True, alpha=0.3, axis='y')

# Route efficiency distribution
ax = axes[0, 1]
ax.hist(lockett_with_time['route_efficiency'], bins=30, color='seagreen', alpha=0.7, edgecolor='black')
ax.axvline(lockett_with_time['route_efficiency'].mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {lockett_with_time["route_efficiency"].mean():.3f}')
ax.set_xlabel('Route Efficiency')
ax.set_ylabel('Frequency')
ax.set_title('Distribution of Route Efficiency')
ax.legend()
ax.grid(True, alpha=0.3, axis='y')

# Time to throw distribution
ax = axes[1, 0]
ax.hist(lockett_with_time['time_to_throw'], bins=30, color='coral', alpha=0.7, edgecolor='black')
ax.axvline(lockett_with_time['time_to_throw'].mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {lockett_with_time["time_to_throw"].mean():.2f}s')
ax.set_xlabel('Time to Throw (seconds)')
ax.set_ylabel('Frequency')
ax.set_title('Distribution of Time to Throw')
ax.legend()
ax.grid(True, alpha=0.3, axis='y')

# Final distance to ball
ax = axes[1, 1]
ax.hist(lockett_with_time['final_dist_to_ball'], bins=30, color='mediumpurple', alpha=0.7, edgecolor='black')
ax.axvline(lockett_with_time['final_dist_to_ball'].mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {lockett_with_time["final_dist_to_ball"].mean():.1f} yds')
ax.set_xlabel('Final Distance to Ball (yards)')
ax.set_ylabel('Frequency')
ax.set_title('Separation at Throw Moment')
ax.legend()
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
fig_path = figures_dir / "lockett_profile.png"
plt.savefig(fig_path, dpi=300, bbox_inches='tight')
log(f"✓ Saved {fig_path}")
plt.close()

log("\n" + "="*80)
log("ANALYSIS COMPLETE")
log("="*80)
log(f"\nResults: {results_dir}")
log(f"Figures: {figures_dir}")
log(f"Log: {log_file}")
