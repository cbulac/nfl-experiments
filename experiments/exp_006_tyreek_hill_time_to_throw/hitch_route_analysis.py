#!/usr/bin/env python3
"""
HITCH Route Analysis Across Receiver Archetypes

Tests hypothesis: Do "Precision Technicians" execute HITCH routes better,
or is it just the only way slow receivers can get open?

Analyzes: timing, depth, separation, completion %, speed, efficiency
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

print("="*80)
print("HITCH ROUTE ANALYSIS: Precision vs Necessity")
print("="*80)

# Load archetype assignments
route_profiles = pd.read_csv(results_dir / "route_frequency_profiles.csv", index_col=0)
print(f"\nLoaded {len(route_profiles)} receiver profiles")

# Load supplementary data
supp_df = pd.read_csv(data_dir / "interim" / "supplementary_data_enhanced.csv", low_memory=False)

# Filter to HITCH routes only
hitch_plays = supp_df[supp_df['route_of_targeted_receiver'] == 'HITCH'].copy()
print(f"Total HITCH route plays: {len(hitch_plays):,}")

# Load tracking data for all receivers
print("\nLoading tracking data for HITCH routes...")
train_dir = data_dir / "raw" / "train"
input_files = sorted(glob.glob(str(train_dir / "input_2023_*.csv")))

target_receivers = route_profiles.index.tolist()
all_hitch_tracking = []

for i, file_path in enumerate(input_files, 1):
    week = file_path.split('_')[-1].replace('.csv', '')
    print(f"  [{i}/{len(input_files)}] Processing week {week}...")

    for chunk in pd.read_csv(file_path, chunksize=100000):
        receiver_chunk = chunk[
            (chunk['player_name'].isin(target_receivers)) &
            (chunk['player_side'] == 'Offense')
        ].copy()

        if len(receiver_chunk) > 0:
            all_hitch_tracking.append(receiver_chunk)

print("\nCombining tracking data...")
tracking_df = pd.concat(all_hitch_tracking, ignore_index=True)
print(f"Total tracking frames: {len(tracking_df):,}")

# Merge with HITCH plays
print("\nMerging tracking with HITCH routes...")
hitch_tracking = tracking_df.merge(
    hitch_plays[['game_id', 'play_id', 'time_to_throw', 'pass_result', 'yards_gained']],
    on=['game_id', 'play_id'],
    how='inner'
)
print(f"HITCH route frames: {len(hitch_tracking):,}")

# Calculate metrics for each HITCH route
print("\n" + "="*80)
print("CALCULATING HITCH ROUTE METRICS")
print("="*80)

play_groups = hitch_tracking.groupby(['player_name', 'game_id', 'play_id'])
hitch_metrics = []

for (player_name, game_id, play_id), group in play_groups:
    group = group.sort_values('frame_id')

    # Get start and end positions
    start_x, start_y = group.iloc[0][['x', 'y']]
    end_x, end_y = group.iloc[-1][['x', 'y']]

    # Calculate route depth (vertical distance traveled)
    route_depth = abs(end_y - start_y)

    # Total distance traveled
    x_diff = group['x'].diff()
    y_diff = group['y'].diff()
    distances = np.sqrt(x_diff**2 + y_diff**2)
    total_distance = distances.sum()

    # Route efficiency
    displacement = np.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
    route_efficiency = displacement / total_distance if total_distance > 0 else 0

    # Speed metrics
    max_speed = group['s'].max()
    avg_speed = group['s'].mean()

    # Speed at route break (typically ~80% of route)
    break_frame = int(len(group) * 0.8)
    if break_frame < len(group):
        speed_at_break = group.iloc[break_frame]['s']
    else:
        speed_at_break = group.iloc[-1]['s']

    # Distance to ball at throw moment
    ball_x = group.iloc[0]['ball_land_x']
    ball_y = group.iloc[0]['ball_land_y']
    final_dist_to_ball = np.sqrt((end_x - ball_x)**2 + (end_y - ball_y)**2)

    # Time to throw
    time_to_throw = group.iloc[0]['time_to_throw']

    # Pass result
    pass_result = group.iloc[0]['pass_result']
    yards_gained = group.iloc[0]['yards_gained']

    hitch_metrics.append({
        'player_name': player_name,
        'game_id': game_id,
        'play_id': play_id,
        'route_depth': route_depth,
        'total_distance': total_distance,
        'displacement': displacement,
        'route_efficiency': route_efficiency,
        'max_speed': max_speed,
        'avg_speed': avg_speed,
        'speed_at_break': speed_at_break,
        'final_dist_to_ball': final_dist_to_ball,
        'time_to_throw': time_to_throw,
        'pass_result': pass_result,
        'yards_gained': yards_gained if pd.notna(yards_gained) else 0
    })

hitch_df = pd.DataFrame(hitch_metrics)
print(f"Calculated metrics for {len(hitch_df):,} HITCH routes")

# Add archetype labels
print("\nAdding archetype labels...")
player_archetype_map = route_profiles['cluster'].to_dict()
hitch_df['archetype'] = hitch_df['player_name'].map(player_archetype_map)

# Map archetype numbers to names
archetype_names = {
    0: 'Precision Technicians',
    1: 'Balanced All-Purpose',
    2: 'Possession Specialists',
    3: 'HITCH Masters',
    4: 'Vertical Threats'
}
hitch_df['archetype_name'] = hitch_df['archetype'].map(archetype_names)

# Calculate completion flag
hitch_df['completed'] = (hitch_df['pass_result'] == 'C').astype(int)

# Remove any NaN archetypes
hitch_df = hitch_df[hitch_df['archetype'].notna()].copy()
print(f"HITCH routes with archetype labels: {len(hitch_df):,}")

# Analyze by archetype
print("\n" + "="*80)
print("HITCH ROUTE PERFORMANCE BY ARCHETYPE")
print("="*80)

archetype_stats = hitch_df.groupby('archetype_name').agg({
    'play_id': 'count',
    'route_depth': ['mean', 'std'],
    'total_distance': ['mean', 'std'],
    'route_efficiency': ['mean', 'std'],
    'max_speed': ['mean', 'std'],
    'avg_speed': ['mean', 'std'],
    'speed_at_break': ['mean', 'std'],
    'final_dist_to_ball': ['mean', 'std'],
    'time_to_throw': ['mean', 'std'],
    'completed': ['sum', 'mean'],
    'yards_gained': 'mean'
}).round(2)

archetype_stats.columns = ['_'.join(col).strip('_') for col in archetype_stats.columns]
archetype_stats = archetype_stats.rename(columns={
    'play_id_count': 'n_routes',
    'completed_sum': 'completions',
    'completed_mean': 'completion_pct'
})
archetype_stats['completion_pct'] = (archetype_stats['completion_pct'] * 100).round(1)

print("\nArchetype Summary:")
print(archetype_stats[['n_routes', 'route_depth_mean', 'max_speed_mean',
                       'final_dist_to_ball_mean', 'completion_pct', 'yards_gained_mean']])

# Statistical tests
print("\n" + "="*80)
print("STATISTICAL SIGNIFICANCE TESTING")
print("="*80)

# Compare Precision Technicians vs others
precision_tech = hitch_df[hitch_df['archetype_name'] == 'Precision Technicians']
others = hitch_df[hitch_df['archetype_name'] != 'Precision Technicians']

metrics_to_test = [
    ('route_depth', 'Route Depth'),
    ('route_efficiency', 'Route Efficiency'),
    ('max_speed', 'Max Speed'),
    ('final_dist_to_ball', 'Separation at Throw'),
    ('time_to_throw', 'Time to Throw'),
    ('completion_pct', 'Completion %')
]

print("\nPrecision Technicians vs All Others:")
for metric, label in metrics_to_test:
    if metric == 'completion_pct':
        # For completion %, use the completed column
        prec_vals = precision_tech['completed']
        other_vals = others['completed']
    else:
        prec_vals = precision_tech[metric].dropna()
        other_vals = others[metric].dropna()

    prec_mean = prec_vals.mean()
    other_mean = other_vals.mean()

    # T-test
    t_stat, p_val = stats.ttest_ind(prec_vals, other_vals, equal_var=False)

    # Effect size (Cohen's d)
    pooled_std = np.sqrt((prec_vals.std()**2 + other_vals.std()**2) / 2)
    cohens_d = (prec_mean - other_mean) / pooled_std if pooled_std > 0 else 0

    sig = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else "ns"

    if metric == 'completion_pct':
        prec_pct = prec_mean * 100
        other_pct = other_mean * 100
        print(f"  {label}: Precision {prec_pct:.1f}% vs Others {other_pct:.1f}% | "
              f"d={cohens_d:.3f} | p={p_val:.4f} {sig}")
    else:
        print(f"  {label}: Precision {prec_mean:.2f} vs Others {other_mean:.2f} | "
              f"d={cohens_d:.3f} | p={p_val:.4f} {sig}")

# Compare HITCH Masters vs Precision Technicians
print("\nHITCH Masters vs Precision Technicians:")
hitch_masters = hitch_df[hitch_df['archetype_name'] == 'HITCH Masters']

for metric, label in metrics_to_test:
    if metric == 'completion_pct':
        hm_vals = hitch_masters['completed']
        pt_vals = precision_tech['completed']
    else:
        hm_vals = hitch_masters[metric].dropna()
        pt_vals = precision_tech[metric].dropna()

    hm_mean = hm_vals.mean()
    pt_mean = pt_vals.mean()

    t_stat, p_val = stats.ttest_ind(hm_vals, pt_vals, equal_var=False)

    pooled_std = np.sqrt((hm_vals.std()**2 + pt_vals.std()**2) / 2)
    cohens_d = (hm_mean - pt_mean) / pooled_std if pooled_std > 0 else 0

    sig = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else "ns"

    if metric == 'completion_pct':
        hm_pct = hm_mean * 100
        pt_pct = pt_mean * 100
        print(f"  {label}: HITCH Masters {hm_pct:.1f}% vs Precision {pt_pct:.1f}% | "
              f"d={cohens_d:.3f} | p={p_val:.4f} {sig}")
    else:
        print(f"  {label}: HITCH Masters {hm_mean:.2f} vs Precision {pt_mean:.2f} | "
              f"d={cohens_d:.3f} | p={p_val:.4f} {sig}")

# Save results
results = {
    'experiment': 'hitch_route_analysis',
    'date': datetime.now().isoformat(),
    'total_hitch_routes': len(hitch_df),
    'archetype_stats': archetype_stats.to_dict(),
    'hypothesis_test': 'Precision Technicians vs necessity-based HITCH usage'
}

results_file = results_dir / "hitch_route_analysis.json"
with open(results_file, 'w') as f:
    json.dump(results, f, indent=2)
print(f"\n✓ Saved results to {results_file}")

# Create visualizations
print("\n" + "="*80)
print("CREATING VISUALIZATIONS")
print("="*80)

# 1. Multi-panel comparison
fig, axes = plt.subplots(2, 3, figsize=(18, 12))
fig.suptitle('HITCH Route Performance by Receiver Archetype', fontsize=16, fontweight='bold')

# Plot 1: Route Depth
ax = axes[0, 0]
archetype_order = archetype_stats.sort_values('route_depth_mean', ascending=False).index
route_depths = [hitch_df[hitch_df['archetype_name'] == arch]['route_depth'].dropna() for arch in archetype_order]
bp = ax.boxplot(route_depths, labels=archetype_order, patch_artist=True)
for patch in bp['boxes']:
    patch.set_facecolor('skyblue')
ax.set_ylabel('Route Depth (yards)')
ax.set_title('Route Depth by Archetype')
ax.set_xticklabels(archetype_order, rotation=45, ha='right', fontsize=8)
ax.grid(True, alpha=0.3, axis='y')

# Plot 2: Max Speed
ax = axes[0, 1]
archetype_order_speed = archetype_stats.sort_values('max_speed_mean', ascending=False).index
speeds = [hitch_df[hitch_df['archetype_name'] == arch]['max_speed'].dropna() for arch in archetype_order_speed]
bp = ax.boxplot(speeds, labels=archetype_order_speed, patch_artist=True)
for patch in bp['boxes']:
    patch.set_facecolor('coral')
ax.set_ylabel('Max Speed (mph)')
ax.set_title('Max Speed by Archetype')
ax.set_xticklabels(archetype_order_speed, rotation=45, ha='right', fontsize=8)
ax.grid(True, alpha=0.3, axis='y')

# Plot 3: Separation at Throw
ax = axes[0, 2]
archetype_order_sep = archetype_stats.sort_values('final_dist_to_ball_mean').index
separations = [hitch_df[hitch_df['archetype_name'] == arch]['final_dist_to_ball'].dropna() for arch in archetype_order_sep]
bp = ax.boxplot(separations, labels=archetype_order_sep, patch_artist=True)
for patch in bp['boxes']:
    patch.set_facecolor('lightgreen')
ax.set_ylabel('Separation at Throw (yards)')
ax.set_title('Separation by Archetype')
ax.set_xticklabels(archetype_order_sep, rotation=45, ha='right', fontsize=8)
ax.grid(True, alpha=0.3, axis='y')

# Plot 4: Completion %
ax = axes[1, 0]
comp_pcts = archetype_stats.sort_values('completion_pct', ascending=False)
ax.bar(range(len(comp_pcts)), comp_pcts['completion_pct'], color='seagreen')
ax.set_xticks(range(len(comp_pcts)))
ax.set_xticklabels(comp_pcts.index, rotation=45, ha='right', fontsize=8)
ax.set_ylabel('Completion %')
ax.set_title('Completion % by Archetype')
ax.grid(True, alpha=0.3, axis='y')

# Plot 5: Route Efficiency
ax = axes[1, 1]
archetype_order_eff = archetype_stats.sort_values('route_efficiency_mean', ascending=False).index
efficiencies = [hitch_df[hitch_df['archetype_name'] == arch]['route_efficiency'].dropna() for arch in archetype_order_eff]
bp = ax.boxplot(efficiencies, labels=archetype_order_eff, patch_artist=True)
for patch in bp['boxes']:
    patch.set_facecolor('mediumpurple')
ax.set_ylabel('Route Efficiency')
ax.set_title('Route Precision by Archetype')
ax.set_xticklabels(archetype_order_eff, rotation=45, ha='right', fontsize=8)
ax.grid(True, alpha=0.3, axis='y')

# Plot 6: Time to Throw
ax = axes[1, 2]
archetype_order_time = archetype_stats.sort_values('time_to_throw_mean').index
times = [hitch_df[hitch_df['archetype_name'] == arch]['time_to_throw'].dropna() for arch in archetype_order_time]
bp = ax.boxplot(times, labels=archetype_order_time, patch_artist=True)
for patch in bp['boxes']:
    patch.set_facecolor('gold')
ax.set_ylabel('Time to Throw (seconds)')
ax.set_title('Timing by Archetype')
ax.set_xticklabels(archetype_order_time, rotation=45, ha='right', fontsize=8)
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
fig_path = figures_dir / "hitch_route_comparison.png"
plt.savefig(fig_path, dpi=300, bbox_inches='tight')
print(f"✓ Saved {fig_path}")
plt.close()

# 2. Speed vs Separation scatter
fig, ax = plt.subplots(figsize=(12, 8))

colors = {'Precision Technicians': 'blue', 'Balanced All-Purpose': 'gray',
          'Possession Specialists': 'green', 'HITCH Masters': 'red',
          'Vertical Threats': 'purple'}

for archetype in hitch_df['archetype_name'].unique():
    if pd.notna(archetype):
        data = hitch_df[hitch_df['archetype_name'] == archetype]
        ax.scatter(data['max_speed'], data['final_dist_to_ball'],
                  alpha=0.4, s=30, color=colors.get(archetype, 'black'),
                  label=archetype)

ax.set_xlabel('Max Speed on HITCH Route (mph)', fontsize=12)
ax.set_ylabel('Separation at Throw (yards)', fontsize=12)
ax.set_title('Speed vs Separation on HITCH Routes', fontsize=14, fontweight='bold')
ax.legend(title='Archetype', loc='best')
ax.grid(True, alpha=0.3)

# Add correlation
corr = hitch_df[['max_speed', 'final_dist_to_ball']].corr().iloc[0, 1]
ax.text(0.05, 0.95, f'Correlation: {corr:.3f}', transform=ax.transAxes,
        fontsize=11, verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
fig_path = figures_dir / "hitch_speed_vs_separation.png"
plt.savefig(fig_path, dpi=300, bbox_inches='tight')
print(f"✓ Saved {fig_path}")
plt.close()

# 3. Summary comparison table visualization
fig, ax = plt.subplots(figsize=(14, 8))
ax.axis('tight')
ax.axis('off')

# Prepare table data
table_data = []
table_data.append(['Archetype', 'N', 'Depth\n(yds)', 'Speed\n(mph)',
                  'Separation\n(yds)', 'Comp %', 'Efficiency'])

for archetype in archetype_stats.index:
    row = [
        archetype,
        int(archetype_stats.loc[archetype, 'n_routes']),
        f"{archetype_stats.loc[archetype, 'route_depth_mean']:.1f}",
        f"{archetype_stats.loc[archetype, 'max_speed_mean']:.2f}",
        f"{archetype_stats.loc[archetype, 'final_dist_to_ball_mean']:.1f}",
        f"{archetype_stats.loc[archetype, 'completion_pct']:.1f}%",
        f"{archetype_stats.loc[archetype, 'route_efficiency_mean']:.3f}"
    ]
    table_data.append(row)

table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                colWidths=[0.25, 0.08, 0.12, 0.12, 0.15, 0.12, 0.12])
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1, 2.5)

# Style header row
for i in range(len(table_data[0])):
    table[(0, i)].set_facecolor('#4CAF50')
    table[(0, i)].set_text_props(weight='bold', color='white')

# Alternate row colors
for i in range(1, len(table_data)):
    for j in range(len(table_data[0])):
        if i % 2 == 0:
            table[(i, j)].set_facecolor('#f0f0f0')

ax.set_title('HITCH Route Performance Summary by Archetype',
             fontsize=14, fontweight='bold', pad=20)

plt.tight_layout()
fig_path = figures_dir / "hitch_summary_table.png"
plt.savefig(fig_path, dpi=300, bbox_inches='tight')
print(f"✓ Saved {fig_path}")
plt.close()

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
print(f"\nResults: {results_dir}")
print(f"Figures: {figures_dir}")
