#!/usr/bin/env python3
"""
HITCH Route Analysis v2 - WITH CORRECT SEPARATION METRICS

Tests hypothesis: Do "Precision Technicians" execute HITCH routes better,
or is it just the only way slow receivers can get open?

Version 2 uses TRUE separation from nearest defender (not distance to ball).

Analyzes: timing, depth, TRUE SEPARATION, completion %, speed, efficiency
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
print("HITCH ROUTE ANALYSIS v2: Precision vs Necessity")
print("WITH CORRECT SEPARATION METRICS")
print("="*80)

# Load archetype assignments
route_profiles = pd.read_csv(results_dir / "route_frequency_profiles.csv", index_col=0)
print(f"\nLoaded {len(route_profiles)} receiver profiles")

# Load defender separation data (THE KEY CHANGE!)
print("\nLoading defender separation data...")
sep_df = pd.read_csv(data_dir / "processed" / "defender_separation.csv")
print(f"Loaded {len(sep_df):,} plays with separation metrics")

# Filter to HITCH routes only
hitch_sep = sep_df[sep_df['route'] == 'HITCH'].copy()
print(f"HITCH routes with separation: {len(hitch_sep):,}")

# Load supplementary data
supp_df = pd.read_csv(data_dir / "interim" / "supplementary_data_enhanced.csv", low_memory=False)

# Filter to HITCH routes only
hitch_plays = supp_df[supp_df['route_of_targeted_receiver'] == 'HITCH'].copy()
print(f"Total HITCH route plays: {len(hitch_plays):,}")

# Merge separation data with supplementary data
hitch_plays = hitch_plays.merge(
    hitch_sep[['game_id', 'play_id', 'receiver_name', 'separation_at_throw',
               'coverage_cushion', 'separation_change', 'defenders_within_3yd',
               'defenders_within_5yd', 'nearest_defender_position']],
    on=['game_id', 'play_id'],
    how='left'
)
print(f"Merged separation data: {hitch_plays['separation_at_throw'].notna().sum():,} HITCH routes with separation")

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
    hitch_plays[['game_id', 'play_id', 'time_to_throw', 'pass_result', 'yards_gained',
                 'separation_at_throw', 'coverage_cushion', 'separation_change',
                 'defenders_within_3yd', 'defenders_within_5yd', 'nearest_defender_position']],
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

    # Time to throw
    time_to_throw = group.iloc[0]['time_to_throw']

    # Pass result
    pass_result = group.iloc[0]['pass_result']
    yards_gained = group.iloc[0]['yards_gained']

    # NEW: Get separation metrics from merged data
    separation_at_throw = group.iloc[0]['separation_at_throw']
    coverage_cushion = group.iloc[0]['coverage_cushion']
    separation_change = group.iloc[0]['separation_change']
    defenders_within_3yd = group.iloc[0]['defenders_within_3yd']
    defenders_within_5yd = group.iloc[0]['defenders_within_5yd']
    nearest_defender_position = group.iloc[0]['nearest_defender_position']

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
        'separation_at_throw': separation_at_throw,  # NEW: TRUE separation
        'coverage_cushion': coverage_cushion,  # NEW
        'separation_change': separation_change,  # NEW
        'defenders_within_3yd': defenders_within_3yd,  # NEW
        'defenders_within_5yd': defenders_within_5yd,  # NEW
        'nearest_defender_position': nearest_defender_position,  # NEW
        'time_to_throw': time_to_throw,
        'pass_result': pass_result,
        'yards_gained': yards_gained if pd.notna(yards_gained) else 0
    })

hitch_df = pd.DataFrame(hitch_metrics)
print(f"Calculated metrics for {len(hitch_df):,} HITCH routes")

# Filter to routes with valid separation data
hitch_df = hitch_df[hitch_df['separation_at_throw'].notna()].copy()
print(f"HITCH routes with valid separation: {len(hitch_df):,}")

# Add archetype labels
print("\nAdding archetype labels...")
player_archetype_map = route_profiles['cluster'].to_dict()
hitch_df['archetype'] = hitch_df['player_name'].map(player_archetype_map)

# Add completion flag
hitch_df['is_complete'] = (hitch_df['pass_result'] == 'C').astype(int)

# Map archetype numbers to names
archetype_names = {
    0: 'Precision Technicians',
    1: 'Balanced All-Purpose',
    2: 'Possession Specialists',
    3: 'HITCH Masters',
    4: 'Vertical Threats'
}
hitch_df['archetype_name'] = hitch_df['archetype'].map(archetype_names)

print("\nHITCH routes by archetype:")
print(hitch_df['archetype_name'].value_counts().sort_index())

# Statistical Analysis
print("\n" + "="*80)
print("STATISTICAL ANALYSIS")
print("="*80)

results = {}

# 1. Overall archetype comparison
print("\n1. HITCH ROUTE METRICS BY ARCHETYPE:")
print("-"*80)

metrics_to_analyze = [
    'separation_at_throw',  # NEW: True separation
    'coverage_cushion',  # NEW
    'separation_change',  # NEW
    'max_speed',
    'route_efficiency',
    'route_depth',
    'time_to_throw'
]

archetype_stats = hitch_df.groupby('archetype_name')[metrics_to_analyze + ['is_complete']].agg({
    'separation_at_throw': ['mean', 'median', 'std'],
    'coverage_cushion': ['mean', 'median'],
    'separation_change': ['mean', 'median'],
    'max_speed': ['mean', 'std'],
    'route_efficiency': ['mean', 'std'],
    'route_depth': ['mean', 'std'],
    'time_to_throw': ['mean', 'std'],
    'is_complete': 'mean'
})

print(archetype_stats)

# Save detailed stats
results['archetype_comparison'] = {}
for archetype in archetype_names.values():
    archetype_data = hitch_df[hitch_df['archetype_name'] == archetype]
    results['archetype_comparison'][archetype] = {
        'n_routes': len(archetype_data),
        'separation_at_throw_mean': float(archetype_data['separation_at_throw'].mean()),
        'separation_at_throw_median': float(archetype_data['separation_at_throw'].median()),
        'separation_at_throw_std': float(archetype_data['separation_at_throw'].std()),
        'coverage_cushion_mean': float(archetype_data['coverage_cushion'].mean()),
        'separation_change_mean': float(archetype_data['separation_change'].mean()),
        'max_speed_mean': float(archetype_data['max_speed'].mean()),
        'route_efficiency_mean': float(archetype_data['route_efficiency'].mean()),
        'route_depth_mean': float(archetype_data['route_depth'].mean()),
        'time_to_throw_mean': float(archetype_data['time_to_throw'].mean()),
        'completion_pct': float(archetype_data['is_complete'].mean() * 100)
    }

# 2. HITCH Masters vs Precision Technicians (HEAD TO HEAD)
print("\n2. HITCH MASTERS vs PRECISION TECHNICIANS:")
print("-"*80)

hitch_masters = hitch_df[hitch_df['archetype_name'] == 'HITCH Masters']
precision_tech = hitch_df[hitch_df['archetype_name'] == 'Precision Technicians']

print(f"\nHITCH Masters: {len(hitch_masters)} routes")
print(f"Precision Technicians: {len(precision_tech)} routes")

comparison_metrics = {
    'separation_at_throw': 'Separation at Throw (yards)',
    'coverage_cushion': 'Coverage Cushion (yards)',
    'separation_change': 'Separation Change (yards)',
    'max_speed': 'Max Speed (mph)',
    'route_efficiency': 'Route Efficiency',
    'route_depth': 'Route Depth (yards)',
    'time_to_throw': 'Time to Throw (seconds)'
}

results['hitch_masters_vs_precision'] = {}

for metric, label in comparison_metrics.items():
    masters_vals = hitch_masters[metric].dropna()
    precision_vals = precision_tech[metric].dropna()

    # Welch's t-test
    t_stat, p_val = stats.ttest_ind(masters_vals, precision_vals, equal_var=False)

    # Cohen's d
    pooled_std = np.sqrt((masters_vals.std()**2 + precision_vals.std()**2) / 2)
    cohens_d = (masters_vals.mean() - precision_vals.mean()) / pooled_std

    masters_mean = masters_vals.mean()
    precision_mean = precision_vals.mean()
    pct_diff = ((masters_mean - precision_mean) / precision_mean) * 100

    print(f"\n{label}:")
    print(f"  HITCH Masters:    {masters_mean:.3f}")
    print(f"  Precision Tech:   {precision_mean:.3f}")
    print(f"  Difference:       {pct_diff:+.1f}%")
    print(f"  p-value:          {p_val:.3f} {'***' if p_val < 0.001 else '**' if p_val < 0.01 else '*' if p_val < 0.05 else 'ns'}")
    print(f"  Cohen's d:        {cohens_d:.3f}")

    results['hitch_masters_vs_precision'][metric] = {
        'hitch_masters_mean': float(masters_mean),
        'precision_tech_mean': float(precision_mean),
        'percent_difference': float(pct_diff),
        'p_value': float(p_val),
        'cohens_d': float(cohens_d),
        'significant': bool(p_val < 0.05)
    }

# Completion percentage
masters_comp = hitch_masters['is_complete'].mean() * 100
precision_comp = precision_tech['is_complete'].mean() * 100
print(f"\nCompletion %:")
print(f"  HITCH Masters:    {masters_comp:.1f}%")
print(f"  Precision Tech:   {precision_comp:.1f}%")
print(f"  Difference:       {masters_comp - precision_comp:+.1f}%")

results['hitch_masters_vs_precision']['completion_pct'] = {
    'hitch_masters': float(masters_comp),
    'precision_tech': float(precision_comp),
    'difference': float(masters_comp - precision_comp)
}

# 3. Precision Technicians vs All Others
print("\n3. PRECISION TECHNICIANS vs ALL OTHERS:")
print("-"*80)

all_others = hitch_df[hitch_df['archetype_name'] != 'Precision Technicians']

results['precision_vs_others'] = {}

for metric, label in comparison_metrics.items():
    precision_vals = precision_tech[metric].dropna()
    others_vals = all_others[metric].dropna()

    t_stat, p_val = stats.ttest_ind(precision_vals, others_vals, equal_var=False)

    precision_mean = precision_vals.mean()
    others_mean = others_vals.mean()
    pct_diff = ((precision_mean - others_mean) / others_mean) * 100

    print(f"\n{label}:")
    print(f"  Precision Tech:   {precision_mean:.3f}")
    print(f"  All Others:       {others_mean:.3f}")
    print(f"  Difference:       {pct_diff:+.1f}%")
    print(f"  p-value:          {p_val:.3f} {'***' if p_val < 0.001 else '**' if p_val < 0.01 else '*' if p_val < 0.05 else 'ns'}")

    results['precision_vs_others'][metric] = {
        'precision_tech_mean': float(precision_mean),
        'all_others_mean': float(others_mean),
        'percent_difference': float(pct_diff),
        'p_value': float(p_val),
        'significant': bool(p_val < 0.05)
    }

# 4. Correlation: Speed vs Separation
print("\n4. CORRELATION: Speed vs Separation:")
print("-"*80)
speed_sep_corr = hitch_df[['max_speed', 'separation_at_throw']].corr().iloc[0, 1]
print(f"Correlation coefficient: {speed_sep_corr:.3f}")
print(f"Interpretation: {'Positive' if speed_sep_corr > 0 else 'Negative'} correlation")
print(f"                Faster receivers create {'MORE' if speed_sep_corr > 0 else 'LESS'} separation")

results['speed_vs_separation_correlation'] = float(speed_sep_corr)

# Save results
output_path = results_dir / "hitch_route_analysis_v2.json"
print(f"\nSaving results to {output_path}")
with open(output_path, 'w') as f:
    json.dump(results, f, indent=2)

# Visualization
print("\n" + "="*80)
print("CREATING VISUALIZATIONS")
print("="*80)

fig, axes = plt.subplots(2, 3, figsize=(18, 12))
fig.suptitle('HITCH Route Performance by Receiver Archetype (v2 - TRUE SEPARATION)',
             fontsize=16, fontweight='bold')

# 1. Separation at Throw
ax = axes[0, 0]
archetype_order = sorted(hitch_df['archetype_name'].unique())
sns.boxplot(data=hitch_df, x='archetype_name', y='separation_at_throw',
            order=archetype_order, ax=ax, palette='Set2')
ax.set_xlabel('')
ax.set_ylabel('Separation (yards)')
ax.set_title('TRUE Separation at Throw')
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
ax.axhline(hitch_df['separation_at_throw'].mean(), color='red', linestyle='--', alpha=0.5)

# 2. Max Speed
ax = axes[0, 1]
sns.boxplot(data=hitch_df, x='archetype_name', y='max_speed',
            order=archetype_order, ax=ax, palette='Set2')
ax.set_xlabel('')
ax.set_ylabel('Max Speed (mph)')
ax.set_title('Max Speed by Archetype')
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')

# 3. Route Efficiency
ax = axes[0, 2]
sns.boxplot(data=hitch_df, x='archetype_name', y='route_efficiency',
            order=archetype_order, ax=ax, palette='Set2')
ax.set_xlabel('')
ax.set_ylabel('Route Efficiency')
ax.set_title('Route Precision by Archetype')
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')

# 4. Completion %
ax = axes[1, 0]
comp_pct = hitch_df.groupby('archetype_name')['is_complete'].mean() * 100
comp_pct = comp_pct.reindex(archetype_order)
bars = ax.bar(range(len(comp_pct)), comp_pct.values, color='green', alpha=0.6)
ax.set_xticks(range(len(comp_pct)))
ax.set_xticklabels(comp_pct.index, rotation=45, ha='right')
ax.set_ylabel('Completion %')
ax.set_title('Completion % by Archetype')
ax.axhline(hitch_df['is_complete'].mean() * 100, color='red', linestyle='--', alpha=0.5)
ax.set_ylim(0, 100)

# 5. Time to Throw
ax = axes[1, 1]
sns.boxplot(data=hitch_df, x='archetype_name', y='time_to_throw',
            order=archetype_order, ax=ax, palette='Set2')
ax.set_xlabel('')
ax.set_ylabel('Time to Throw (seconds)')
ax.set_title('Timing by Archetype')
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')

# 6. Speed vs Separation Scatter
ax = axes[1, 2]
for archetype in archetype_order:
    data = hitch_df[hitch_df['archetype_name'] == archetype]
    ax.scatter(data['max_speed'], data['separation_at_throw'],
              label=archetype, alpha=0.5, s=20)
ax.set_xlabel('Max Speed (mph)')
ax.set_ylabel('Separation at Throw (yards)')
ax.set_title(f'Speed vs Separation (r={speed_sep_corr:.2f})')
ax.legend(fontsize=8, loc='best')

plt.tight_layout()
fig_path = figures_dir / "hitch_route_comparison_v2.png"
plt.savefig(fig_path, dpi=300, bbox_inches='tight')
print(f"Saved figure: {fig_path}")

# Summary Table Figure
fig, ax = plt.subplots(figsize=(14, 8))
ax.axis('off')

summary_data = []
for archetype in archetype_order:
    data = hitch_df[hitch_df['archetype_name'] == archetype]
    summary_data.append([
        archetype,
        f"{len(data)}",
        f"{data['separation_at_throw'].mean():.2f}",
        f"{data['max_speed'].mean():.2f}",
        f"{data['route_efficiency'].mean():.3f}",
        f"{data['time_to_throw'].mean():.2f}",
        f"{data['is_complete'].mean()*100:.1f}%"
    ])

table = ax.table(cellText=summary_data,
                colLabels=['Archetype', 'N', 'Sep (yds)', 'Speed (mph)',
                          'Efficiency', 'Time (s)', 'Comp %'],
                cellLoc='center',
                loc='center',
                bbox=[0, 0, 1, 1])
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1, 2)

# Style header row
for i in range(7):
    table[(0, i)].set_facecolor('#40466e')
    table[(0, i)].set_text_props(weight='bold', color='white')

# Highlight best values
for i, row in enumerate(summary_data, 1):
    # Highlight HITCH Masters row
    if 'HITCH Masters' in row[0]:
        for j in range(7):
            table[(i, j)].set_facecolor('#90EE90')
    # Highlight Precision Technicians row
    elif 'Precision Technicians' in row[0]:
        for j in range(7):
            table[(i, j)].set_facecolor('#FFB6C1')

plt.title('HITCH Route Summary by Archetype (v2 - TRUE SEPARATION)',
          fontsize=14, fontweight='bold', pad=20)

table_path = figures_dir / "hitch_summary_table_v2.png"
plt.savefig(table_path, dpi=300, bbox_inches='tight')
print(f"Saved table: {table_path}")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
print(f"\nResults saved to: {output_path}")
print(f"Figures saved to: {figures_dir}")
print("\nKey Findings:")
print(f"- HITCH Masters separation: {hitch_masters['separation_at_throw'].mean():.2f} yards")
print(f"- Precision Tech separation: {precision_tech['separation_at_throw'].mean():.2f} yards")
print(f"- Difference: {((hitch_masters['separation_at_throw'].mean() - precision_tech['separation_at_throw'].mean()) / precision_tech['separation_at_throw'].mean() * 100):+.1f}%")
print(f"- Speed vs Separation correlation: {speed_sep_corr:.3f}")
