#!/usr/bin/env python3
"""
Experiment 006: Tyreek Hill Route Completion vs Time to Throw

Analyzes relationship between time to throw and WR's ability to complete routes,
using Tyreek Hill as case study for elite WR route running.
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
log_file = logs_dir / f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_run.log"

def log(message):
    """Log message to both console and file"""
    print(message)
    with open(log_file, 'a') as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

log("="*80)
log("Experiment 006: Tyreek Hill Route Completion vs Time to Throw")
log("="*80)

# Load enhanced supplementary data
log("\nLoading enhanced supplementary data with time_to_throw...")
supp_path = data_dir / "interim" / "supplementary_data_enhanced.csv"
supp_df = pd.read_csv(supp_path, low_memory=False)
log(f"Loaded {len(supp_df):,} plays")
log(f"Plays with time_to_throw: {supp_df['time_to_throw'].notna().sum():,}")

# Load all tracking data to get Tyreek Hill plays
log("\nLoading tracking data for Tyreek Hill...")
train_dir = data_dir / "raw" / "train"
input_files = sorted(glob.glob(str(train_dir / "input_2023_*.csv")))

all_tyreek_data = []
for i, file_path in enumerate(input_files, 1):
    week = file_path.split('_')[-1].replace('.csv', '')
    log(f"  [{i}/{len(input_files)}] Processing week {week}...")

    # Read chunk by chunk to find Tyreek
    for chunk in pd.read_csv(file_path, chunksize=100000):
        tyreek_chunk = chunk[chunk['player_name'] == 'Tyreek Hill'].copy()
        if len(tyreek_chunk) > 0:
            all_tyreek_data.append(tyreek_chunk)

log("\nCombining Tyreek Hill tracking data...")
tyreek_df = pd.concat(all_tyreek_data, ignore_index=True)
log(f"Total Tyreek Hill frames: {len(tyreek_df):,}")
log(f"Unique plays: {tyreek_df['play_id'].nunique():,}")

# Calculate route metrics for each play
log("\nCalculating route completion metrics...")

# Group by play
play_groups = tyreek_df.groupby(['game_id', 'play_id'])

route_metrics = []
for (game_id, play_id), group in play_groups:
    # Sort by frame to get trajectory
    group = group.sort_values('frame_id')

    # Calculate total distance traveled (route length)
    x_diff = group['x'].diff()
    y_diff = group['y'].diff()
    distances = np.sqrt(x_diff**2 + y_diff**2)
    total_distance = distances.sum()

    # Get start and end positions
    start_x, start_y = group.iloc[0][['x', 'y']]
    end_x, end_y = group.iloc[-1][['x', 'y']]

    # Calculate displacement (straight line from start to end)
    displacement = np.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)

    # Route efficiency: displacement / total_distance
    # Higher = more direct route, Lower = more cuts/changes
    route_efficiency = displacement / total_distance if total_distance > 0 else 0

    # Max speed during route
    max_speed = group['s'].max()
    avg_speed = group['s'].mean()

    # Max acceleration
    max_accel = group['a'].max()

    # Distance to ball at end (catch point or target)
    ball_x = group.iloc[0]['ball_land_x']
    ball_y = group.iloc[0]['ball_land_y']
    final_dist_to_ball = np.sqrt((end_x - ball_x)**2 + (end_y - ball_y)**2)

    # Number of frames
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
log(f"Calculated metrics for {len(route_df):,} Tyreek Hill plays")

# Merge with supplementary data to get route types and time_to_throw
log("\nMerging with supplementary data...")
tyreek_analysis = route_df.merge(
    supp_df[['game_id', 'play_id', 'route_of_targeted_receiver', 'time_to_throw',
             'pass_result', 'yards_gained', 'pass_length', 'team_coverage_type',
             'play_description']],
    on=['game_id', 'play_id'],
    how='left'
)

# Filter to plays where Tyreek was targeted
tyreek_targeted = tyreek_analysis[tyreek_analysis['route_of_targeted_receiver'].notna()].copy()
log(f"Plays where Tyreek was targeted: {len(tyreek_targeted):,}")

# Filter to plays with time_to_throw data
tyreek_with_time = tyreek_targeted[tyreek_targeted['time_to_throw'].notna()].copy()
log(f"Targeted plays with time_to_throw: {len(tyreek_with_time):,}")

# Analyze by route type
log("\n" + "="*80)
log("ROUTE COMPLETION ANALYSIS")
log("="*80)

# Group by route type
route_summary = tyreek_with_time.groupby('route_of_targeted_receiver').agg({
    'play_id': 'count',
    'time_to_throw': ['mean', 'std'],
    'route_efficiency': ['mean', 'std'],
    'total_distance': ['mean', 'std'],
    'displacement': ['mean', 'std'],
    'max_speed': ['mean', 'max'],
    'final_dist_to_ball': ['mean', 'std'],
    'pass_result': lambda x: (x == 'C').sum(),  # Completions
}).round(2)

route_summary.columns = ['_'.join(col).strip('_') for col in route_summary.columns]
route_summary = route_summary.rename(columns={'play_id_count': 'targets'})
route_summary['completion_pct'] = (route_summary['pass_result_<lambda>'] / route_summary['targets'] * 100).round(1)
route_summary = route_summary.sort_values('targets', ascending=False)

log("\nRoute Type Summary:")
log(route_summary.to_string())

# Time to throw bins
log("\n" + "="*80)
log("TIME TO THROW BINS ANALYSIS")
log("="*80)

# Create time bins
bins = [0, 2.0, 2.5, 3.0, 3.5, 15]
labels = ['Quick (<2s)', 'Fast (2-2.5s)', 'Normal (2.5-3s)', 'Slow (3-3.5s)', 'Very Slow (>3.5s)']
tyreek_with_time['time_bin'] = pd.cut(tyreek_with_time['time_to_throw'], bins=bins, labels=labels)

time_bin_summary = tyreek_with_time.groupby('time_bin').agg({
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

log("\nTime to Throw Bin Summary:")
log(time_bin_summary.to_string())

# Statistical analysis: Correlation
log("\n" + "="*80)
log("CORRELATION ANALYSIS")
log("="*80)

correlations = tyreek_with_time[['time_to_throw', 'route_efficiency', 'total_distance',
                                  'displacement', 'max_speed', 'final_dist_to_ball']].corr()['time_to_throw'].sort_values(ascending=False)
log("\nCorrelations with time_to_throw:")
log(correlations.to_string())

# Save results
log("\n" + "="*80)
log("SAVING RESULTS")
log("="*80)

results = {
    'experiment': 'exp_006_tyreek_hill_time_to_throw',
    'date': datetime.now().isoformat(),
    'player': 'Tyreek Hill',
    'total_plays': len(tyreek_df.groupby(['game_id', 'play_id'])),
    'targeted_plays': len(tyreek_targeted),
    'plays_with_time_data': len(tyreek_with_time),
    'route_summary': route_summary.to_dict(),
    'time_bin_summary': time_bin_summary.to_dict(),
    'correlations': correlations.to_dict(),
    'key_findings': {
        'avg_time_to_throw': float(tyreek_with_time['time_to_throw'].mean()),
        'avg_route_efficiency': float(tyreek_with_time['route_efficiency'].mean()),
        'avg_total_distance': float(tyreek_with_time['total_distance'].mean()),
        'avg_max_speed': float(tyreek_with_time['max_speed'].mean()),
        'overall_completion_pct': float((tyreek_with_time['pass_result'] == 'C').sum() / len(tyreek_with_time) * 100)
    }
}

results_file = results_dir / "tyreek_analysis.json"
with open(results_file, 'w') as f:
    json.dump(results, f, indent=2)
log(f"✓ Saved results to {results_file}")

# Create visualizations
log("\nCreating visualizations...")

# 1. Time to throw vs route metrics
fig, axes = plt.subplots(2, 3, figsize=(18, 12))
fig.suptitle('Tyreek Hill: Route Metrics vs Time to Throw', fontsize=16, fontweight='bold')

# Plot 1: Route Efficiency vs Time to Throw
ax = axes[0, 0]
scatter = ax.scatter(tyreek_with_time['time_to_throw'], tyreek_with_time['route_efficiency'],
                     c=tyreek_with_time['pass_result'].map({'C': 'green', 'I': 'red', 'IN': 'orange'}),
                     alpha=0.6, s=50)
ax.set_xlabel('Time to Throw (seconds)')
ax.set_ylabel('Route Efficiency (displacement/distance)')
ax.set_title('Route Efficiency vs Time to Throw')
ax.grid(True, alpha=0.3)

# Add trend line
z = np.polyfit(tyreek_with_time['time_to_throw'], tyreek_with_time['route_efficiency'], 1)
p = np.poly1d(z)
ax.plot(tyreek_with_time['time_to_throw'].sort_values(),
        p(tyreek_with_time['time_to_throw'].sort_values()),
        "r--", alpha=0.8, linewidth=2, label=f'Trend: y={z[0]:.3f}x+{z[1]:.3f}')
ax.legend()

# Plot 2: Total Distance vs Time to Throw
ax = axes[0, 1]
ax.scatter(tyreek_with_time['time_to_throw'], tyreek_with_time['total_distance'],
           c=tyreek_with_time['pass_result'].map({'C': 'green', 'I': 'red', 'IN': 'orange'}),
           alpha=0.6, s=50)
ax.set_xlabel('Time to Throw (seconds)')
ax.set_ylabel('Total Distance Traveled (yards)')
ax.set_title('Total Route Distance vs Time to Throw')
ax.grid(True, alpha=0.3)

# Add trend line
z = np.polyfit(tyreek_with_time['time_to_throw'], tyreek_with_time['total_distance'], 1)
p = np.poly1d(z)
ax.plot(tyreek_with_time['time_to_throw'].sort_values(),
        p(tyreek_with_time['time_to_throw'].sort_values()),
        "r--", alpha=0.8, linewidth=2, label=f'Trend: y={z[0]:.3f}x+{z[1]:.3f}')
ax.legend()

# Plot 3: Max Speed vs Time to Throw
ax = axes[0, 2]
ax.scatter(tyreek_with_time['time_to_throw'], tyreek_with_time['max_speed'],
           c=tyreek_with_time['pass_result'].map({'C': 'green', 'I': 'red', 'IN': 'orange'}),
           alpha=0.6, s=50)
ax.set_xlabel('Time to Throw (seconds)')
ax.set_ylabel('Max Speed (mph)')
ax.set_title('Max Speed vs Time to Throw')
ax.grid(True, alpha=0.3)

# Plot 4: Completion % by Time Bin
ax = axes[1, 0]
time_bin_summary.reset_index()[['time_bin', 'completion_pct']].plot(
    kind='bar', x='time_bin', y='completion_pct', ax=ax, legend=False, color='skyblue'
)
ax.set_xlabel('Time to Throw Bin')
ax.set_ylabel('Completion %')
ax.set_title('Completion % by Time to Throw')
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
ax.grid(True, alpha=0.3, axis='y')

# Plot 5: Route Distance by Time Bin
ax = axes[1, 1]
time_bin_summary.reset_index()[['time_bin', 'avg_total_distance']].plot(
    kind='bar', x='time_bin', y='avg_total_distance', ax=ax, legend=False, color='coral'
)
ax.set_xlabel('Time to Throw Bin')
ax.set_ylabel('Avg Total Distance (yards)')
ax.set_title('Route Distance by Time to Throw')
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
ax.grid(True, alpha=0.3, axis='y')

# Plot 6: Route Efficiency by Time Bin
ax = axes[1, 2]
time_bin_summary.reset_index()[['time_bin', 'avg_route_efficiency']].plot(
    kind='bar', x='time_bin', y='avg_route_efficiency', ax=ax, legend=False, color='lightgreen'
)
ax.set_xlabel('Time to Throw Bin')
ax.set_ylabel('Avg Route Efficiency')
ax.set_title('Route Efficiency by Time to Throw')
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
fig_path = figures_dir / "tyreek_time_to_throw_analysis.png"
plt.savefig(fig_path, dpi=300, bbox_inches='tight')
log(f"✓ Saved figure to {fig_path}")
plt.close()

# 2. Route type analysis
fig, axes = plt.subplots(1, 2, figsize=(16, 6))
fig.suptitle('Tyreek Hill: Route Type Analysis', fontsize=16, fontweight='bold')

# Top routes by frequency
top_routes = route_summary.nlargest(10, 'targets')

ax = axes[0]
top_routes['targets'].plot(kind='barh', ax=ax, color='steelblue')
ax.set_xlabel('Number of Targets')
ax.set_ylabel('Route Type')
ax.set_title('Top 10 Routes by Frequency')
ax.grid(True, alpha=0.3, axis='x')

# Completion % by route
ax = axes[1]
top_routes['completion_pct'].plot(kind='barh', ax=ax, color='seagreen')
ax.set_xlabel('Completion %')
ax.set_ylabel('Route Type')
ax.set_title('Completion % by Route Type (Top 10)')
ax.grid(True, alpha=0.3, axis='x')

plt.tight_layout()
fig_path = figures_dir / "tyreek_route_types.png"
plt.savefig(fig_path, dpi=300, bbox_inches='tight')
log(f"✓ Saved figure to {fig_path}")
plt.close()

log("\n" + "="*80)
log("ANALYSIS COMPLETE")
log("="*80)
log(f"\nResults saved to: {results_dir}")
log(f"Figures saved to: {figures_dir}")
log(f"Log saved to: {log_file}")
