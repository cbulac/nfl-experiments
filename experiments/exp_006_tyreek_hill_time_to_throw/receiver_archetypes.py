#!/usr/bin/env python3
"""
Receiver Archetype Analysis: Route Frequency Clustering

Generates player profiles based on route frequency patterns and clusters
receivers into archetypes. Finds similar receivers to Tyreek Hill and Tyler Lockett.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
import json
import glob
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist, squareform

# Setup paths
exp_dir = Path(__file__).parent
project_root = exp_dir.parent.parent
data_dir = project_root / "data"
results_dir = exp_dir / "results"
figures_dir = results_dir / "figures"

print("="*80)
print("RECEIVER ARCHETYPE ANALYSIS: Route Frequency Clustering")
print("="*80)

# Load supplementary data
print("\nLoading supplementary data...")
supp_df = pd.read_csv(data_dir / "interim" / "supplementary_data_enhanced.csv", low_memory=False)

# Load top receivers
top_receivers_df = pd.read_csv(data_dir / "interim" / "top_receivers_by_team.csv")
print(f"Loaded {len(top_receivers_df)} top receivers")

# Filter to targeted plays
targeted_plays = supp_df[supp_df['route_of_targeted_receiver'].notna()].copy()
print(f"Total targeted plays: {len(targeted_plays):,}")

# Load tracking data to get receiver names for plays
print("\nLoading tracking data for route assignment...")
train_dir = data_dir / "raw" / "train"
input_files = sorted(glob.glob(str(train_dir / "input_2023_*.csv")))

target_receivers = top_receivers_df['player_name'].tolist()
receiver_plays = []

for i, file_path in enumerate(input_files, 1):
    week = file_path.split('_')[-1].replace('.csv', '')
    print(f"  [{i}/{len(input_files)}] Processing week {week}...")

    for chunk in pd.read_csv(file_path, chunksize=100000,
                             usecols=['game_id', 'play_id', 'player_name', 'player_side']):
        receivers = chunk[
            (chunk['player_name'].isin(target_receivers)) &
            (chunk['player_side'] == 'Offense')
        ][['game_id', 'play_id', 'player_name']].drop_duplicates()

        if len(receivers) > 0:
            receiver_plays.append(receivers)

print("\nCombining receiver-play data...")
all_receiver_plays = pd.concat(receiver_plays, ignore_index=True)

# Merge with targeted plays
print("\nMerging with route data...")
route_data = targeted_plays.merge(
    all_receiver_plays,
    on=['game_id', 'play_id'],
    how='inner'
)
print(f"Total receiver-route combinations: {len(route_data):,}")

# Calculate route frequency for each player
print("\n" + "="*80)
print("CALCULATING ROUTE FREQUENCY PROFILES")
print("="*80)

# Get route counts per player
route_counts = route_data.groupby(['player_name', 'route_of_targeted_receiver']).size().unstack(fill_value=0)
print(f"\nRoute types found: {route_counts.shape[1]}")
print(f"Players analyzed: {route_counts.shape[0]}")

# Calculate percentages
route_percentages = route_counts.div(route_counts.sum(axis=1), axis=0) * 100

# Add total targets
route_percentages['total_targets'] = route_counts.sum(axis=1)

# Sort by total targets
route_percentages = route_percentages.sort_values('total_targets', ascending=False)

print("\nRoute frequency profiles created for all receivers")
print(f"Top 10 receivers by targets:")
print(route_percentages['total_targets'].head(10))

# Calculate similarity matrix (cosine similarity based on route percentages)
print("\n" + "="*80)
print("CALCULATING PLAYER SIMILARITY")
print("="*80)

# Get just the route percentage columns (exclude total_targets)
route_cols = [col for col in route_percentages.columns if col != 'total_targets']
route_profile_matrix = route_percentages[route_cols].values

# Normalize for clustering
scaler = StandardScaler()
route_profile_normalized = scaler.fit_transform(route_profile_matrix)

# Calculate pairwise cosine similarity
from sklearn.metrics.pairwise import cosine_similarity
similarity_matrix = cosine_similarity(route_profile_matrix)
similarity_df = pd.DataFrame(
    similarity_matrix,
    index=route_percentages.index,
    columns=route_percentages.index
)

print("\nSimilarity matrix calculated")

# Find most similar receivers to Tyreek Hill and Tyler Lockett
print("\n" + "="*80)
print("FINDING SIMILAR RECEIVERS")
print("="*80)

def find_similar_receivers(player_name, similarity_df, n=5):
    """Find n most similar receivers to given player"""
    if player_name not in similarity_df.index:
        return None

    similarities = similarity_df[player_name].sort_values(ascending=False)
    # Exclude the player themselves
    similar = similarities[similarities.index != player_name].head(n)
    return similar

# Tyreek Hill
print("\nMost similar to TYREEK HILL:")
tyreek_similar = find_similar_receivers('Tyreek Hill', similarity_df, n=10)
if tyreek_similar is not None:
    for i, (player, score) in enumerate(tyreek_similar.items(), 1):
        print(f"  {i}. {player}: {score:.3f} similarity")

# Tyler Lockett
print("\nMost similar to TYLER LOCKETT:")
lockett_similar = find_similar_receivers('Tyler Lockett', similarity_df, n=10)
if lockett_similar is not None:
    for i, (player, score) in enumerate(lockett_similar.items(), 1):
        print(f"  {i}. {player}: {score:.3f} similarity")

# Perform K-means clustering
print("\n" + "="*80)
print("CLUSTERING RECEIVERS INTO ARCHETYPES")
print("="*80)

# Try different numbers of clusters
inertias = []
for k in range(2, 11):
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(route_profile_normalized)
    inertias.append(kmeans.inertia_)

# Use 5 clusters (good balance)
n_clusters = 5
kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
cluster_labels = kmeans.fit_predict(route_profile_normalized)

# Add cluster labels to dataframe
route_percentages['cluster'] = cluster_labels

print(f"\nClustered receivers into {n_clusters} archetypes")

# Analyze each cluster
print("\n" + "="*80)
print("ARCHETYPE ANALYSIS")
print("="*80)

cluster_profiles = {}
for cluster_id in range(n_clusters):
    cluster_players = route_percentages[route_percentages['cluster'] == cluster_id]
    print(f"\n{'='*60}")
    print(f"ARCHETYPE {cluster_id + 1} ({len(cluster_players)} receivers)")
    print(f"{'='*60}")

    # Get average route distribution
    avg_routes = cluster_players[route_cols].mean().sort_values(ascending=False)
    print("\nTop routes by frequency:")
    for route, pct in avg_routes.head(5).items():
        print(f"  {route}: {pct:.1f}%")

    print("\nReceivers in this archetype:")
    for player in cluster_players.index:
        targets = cluster_players.loc[player, 'total_targets']
        print(f"  - {player} ({int(targets)} targets)")

    cluster_profiles[f"Archetype_{cluster_id + 1}"] = {
        'players': cluster_players.index.tolist(),
        'top_routes': avg_routes.head(5).to_dict(),
        'avg_routes': avg_routes.to_dict()
    }

# Identify which archetype Tyreek and Lockett belong to
tyreek_archetype = route_percentages.loc['Tyreek Hill', 'cluster'] + 1 if 'Tyreek Hill' in route_percentages.index else None
lockett_archetype = route_percentages.loc['Tyler Lockett', 'cluster'] + 1 if 'Tyler Lockett' in route_percentages.index else None

print("\n" + "="*80)
print("KEY PLAYERS ARCHETYPE ASSIGNMENT")
print("="*80)
print(f"Tyreek Hill: Archetype {tyreek_archetype}")
print(f"Tyler Lockett: Archetype {lockett_archetype}")

# Save results
results = {
    'experiment': 'receiver_archetypes',
    'date': datetime.now().isoformat(),
    'n_clusters': n_clusters,
    'n_receivers': len(route_percentages),
    'tyreek_hill': {
        'archetype': int(tyreek_archetype) if tyreek_archetype else None,
        'similar_receivers': tyreek_similar.to_dict() if tyreek_similar is not None else None
    },
    'tyler_lockett': {
        'archetype': int(lockett_archetype) if lockett_archetype else None,
        'similar_receivers': lockett_similar.to_dict() if lockett_similar is not None else None
    },
    'archetypes': cluster_profiles
}

results_file = results_dir / "receiver_archetypes.json"
with open(results_file, 'w') as f:
    json.dump(results, f, indent=2)
print(f"\n✓ Saved results to {results_file}")

# Save route profiles
route_profiles_file = results_dir / "route_frequency_profiles.csv"
route_percentages.to_csv(route_profiles_file)
print(f"✓ Saved route profiles to {route_profiles_file}")

# Create visualizations
print("\n" + "="*80)
print("CREATING VISUALIZATIONS")
print("="*80)

# 1. Heatmap of route frequencies by cluster
fig, ax = plt.subplots(figsize=(16, 12))

# Sort by cluster
route_percentages_sorted = route_percentages.sort_values('cluster')

# Create heatmap (exclude total_targets and cluster columns)
plot_data = route_percentages_sorted[route_cols]

sns.heatmap(plot_data, cmap='YlOrRd', annot=False, fmt='.1f',
            yticklabels=route_percentages_sorted.index,
            cbar_kws={'label': 'Route Frequency (%)'},
            ax=ax)

# Add cluster boundaries
cluster_changes = route_percentages_sorted['cluster'].diff().fillna(0)
boundary_indices = cluster_changes[cluster_changes != 0].index
for idx in boundary_indices:
    pos = list(route_percentages_sorted.index).index(idx)
    ax.axhline(y=pos, color='blue', linewidth=3)

ax.set_title('Receiver Route Frequency Profiles (Grouped by Archetype)', fontsize=14, fontweight='bold')
ax.set_xlabel('Route Type', fontsize=12)
ax.set_ylabel('Receiver', fontsize=12)

plt.tight_layout()
fig_path = figures_dir / "route_frequency_heatmap.png"
plt.savefig(fig_path, dpi=300, bbox_inches='tight')
print(f"✓ Saved {fig_path}")
plt.close()

# 2. Similarity matrix for top 20 receivers
fig, ax = plt.subplots(figsize=(14, 12))

# Get top 20 by targets
top_20 = route_percentages.nlargest(20, 'total_targets').index
similarity_top20 = similarity_df.loc[top_20, top_20]

sns.heatmap(similarity_top20, cmap='coolwarm', annot=True, fmt='.2f',
            square=True, cbar_kws={'label': 'Cosine Similarity'},
            ax=ax, vmin=0.5, vmax=1.0)

ax.set_title('Route Profile Similarity Matrix (Top 20 Receivers)', fontsize=14, fontweight='bold')

plt.tight_layout()
fig_path = figures_dir / "similarity_matrix.png"
plt.savefig(fig_path, dpi=300, bbox_inches='tight')
print(f"✓ Saved {fig_path}")
plt.close()

# 3. Dendrogram for hierarchical clustering
fig, ax = plt.subplots(figsize=(16, 8))

# Perform hierarchical clustering
linkage_matrix = linkage(route_profile_normalized, method='ward')

# Create dendrogram
dendrogram(linkage_matrix, labels=route_percentages.index,
           ax=ax, leaf_font_size=8)

ax.set_title('Receiver Archetype Dendrogram (Hierarchical Clustering)', fontsize=14, fontweight='bold')
ax.set_xlabel('Receiver', fontsize=12)
ax.set_ylabel('Distance', fontsize=12)

plt.tight_layout()
fig_path = figures_dir / "receiver_dendrogram.png"
plt.savefig(fig_path, dpi=300, bbox_inches='tight')
print(f"✓ Saved {fig_path}")
plt.close()

# 4. Archetype radar charts
fig, axes = plt.subplots(2, 3, figsize=(18, 12), subplot_kw=dict(projection='polar'))
axes = axes.flatten()

for cluster_id in range(n_clusters):
    ax = axes[cluster_id]

    cluster_players = route_percentages[route_percentages['cluster'] == cluster_id]
    avg_routes = cluster_players[route_cols].mean()

    # Get top 8 routes
    top_routes = avg_routes.nlargest(8)

    # Prepare data for radar chart
    categories = list(top_routes.index)
    values = list(top_routes.values)

    # Number of variables
    N = len(categories)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    values += values[:1]  # Complete the circle
    angles += angles[:1]

    # Plot
    ax.plot(angles, values, 'o-', linewidth=2)
    ax.fill(angles, values, alpha=0.25)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, size=8)
    ax.set_ylim(0, max(values) * 1.2)
    ax.set_title(f'Archetype {cluster_id + 1}\n({len(cluster_players)} receivers)',
                 fontsize=12, fontweight='bold', pad=20)
    ax.grid(True)

# Remove extra subplot
if n_clusters < 6:
    fig.delaxes(axes[5])

fig.suptitle('Receiver Archetype Route Profiles', fontsize=16, fontweight='bold')
plt.tight_layout()
fig_path = figures_dir / "archetype_radar_charts.png"
plt.savefig(fig_path, dpi=300, bbox_inches='tight')
print(f"✓ Saved {fig_path}")
plt.close()

# 5. Tyreek vs Similar Receivers comparison
if tyreek_similar is not None:
    fig, ax = plt.subplots(figsize=(14, 8))

    # Get Tyreek and top 5 similar
    comparison_players = ['Tyreek Hill'] + list(tyreek_similar.head(5).index)
    comparison_data = route_percentages.loc[comparison_players, route_cols]

    comparison_data.T.plot(kind='bar', ax=ax, width=0.8)

    ax.set_title('Tyreek Hill vs Most Similar Receivers: Route Distribution', fontsize=14, fontweight='bold')
    ax.set_xlabel('Route Type', fontsize=12)
    ax.set_ylabel('Frequency (%)', fontsize=12)
    ax.legend(title='Receiver', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, alpha=0.3, axis='y')

    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    fig_path = figures_dir / "tyreek_similar_comparison.png"
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved {fig_path}")
    plt.close()

# 6. Lockett vs Similar Receivers comparison
if lockett_similar is not None:
    fig, ax = plt.subplots(figsize=(14, 8))

    comparison_players = ['Tyler Lockett'] + list(lockett_similar.head(5).index)
    comparison_data = route_percentages.loc[comparison_players, route_cols]

    comparison_data.T.plot(kind='bar', ax=ax, width=0.8)

    ax.set_title('Tyler Lockett vs Most Similar Receivers: Route Distribution', fontsize=14, fontweight='bold')
    ax.set_xlabel('Route Type', fontsize=12)
    ax.set_ylabel('Frequency (%)', fontsize=12)
    ax.legend(title='Receiver', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, alpha=0.3, axis='y')

    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    fig_path = figures_dir / "lockett_similar_comparison.png"
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved {fig_path}")
    plt.close()

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
print(f"\nResults: {results_dir}")
print(f"Figures: {figures_dir}")
