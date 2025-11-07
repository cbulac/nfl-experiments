#!/usr/bin/env python3
"""
Identify the most targeted receiver for each NFL team in 2023 season
"""

import pandas as pd
from pathlib import Path
import glob

# Paths
project_root = Path(__file__).parent.parent
data_dir = project_root / "data"
train_dir = data_dir / "raw" / "train"
supp_path = data_dir / "raw" / "supplementary_data.csv"

print("Loading supplementary data...")
supp_df = pd.read_csv(supp_path, low_memory=False)

# Get plays where a receiver was targeted
targeted_plays = supp_df[supp_df['route_of_targeted_receiver'].notna()].copy()
print(f"Total plays with targeted receiver: {len(targeted_plays):,}")

# Load tracking data to get receiver names
print("\nLoading tracking data to identify receivers...")
input_files = sorted(glob.glob(str(train_dir / "input_2023_*.csv")))

# First pass: get all unique play_ids with receiver info
receiver_data = []

for i, file_path in enumerate(input_files, 1):
    week = file_path.split('_')[-1].replace('.csv', '')
    print(f"  [{i}/{len(input_files)}] Processing week {week}...")

    # Read in chunks
    for chunk in pd.read_csv(file_path, chunksize=100000,
                             usecols=['game_id', 'play_id', 'player_name',
                                     'player_position', 'player_side']):
        # Filter to offensive WRs/TEs
        receivers = chunk[
            (chunk['player_side'] == 'Offense') &
            (chunk['player_position'].isin(['WR', 'TE']))
        ].copy()

        if len(receivers) > 0:
            receiver_data.append(receivers[['game_id', 'play_id', 'player_name',
                                           'player_position']].drop_duplicates())

print("\nCombining receiver data...")
all_receivers = pd.concat(receiver_data, ignore_index=True)
print(f"Total receiver-play combinations: {len(all_receivers):,}")

# Merge with targeted plays to get team info
print("\nMerging with play data to get team assignments...")
targeted_with_receivers = targeted_plays.merge(
    all_receivers,
    on=['game_id', 'play_id'],
    how='inner'
)

# For each play, we need to determine which team the receiver belongs to
# Use possession_team to identify the offensive team
print("\nIdentifying team for each receiver...")

# Group by receiver and count targets per team
receiver_targets = targeted_with_receivers.groupby(
    ['player_name', 'possession_team', 'player_position']
).size().reset_index(name='targets')

# Get the team with most targets for each receiver (handles trades)
top_team_per_receiver = receiver_targets.loc[
    receiver_targets.groupby('player_name')['targets'].idxmax()
]

# Get top receiver per team
print("\nFinding most targeted receiver for each team...")
top_receiver_per_team = receiver_targets.loc[
    receiver_targets.groupby('possession_team')['targets'].idxmax()
].sort_values('targets', ascending=False)

print("\n" + "="*80)
print("MOST TARGETED RECEIVER PER TEAM (2023 Season)")
print("="*80)
print(top_receiver_per_team.to_string(index=False))

# Save to CSV
output_path = data_dir / "interim" / "top_receivers_by_team.csv"
top_receiver_per_team.to_csv(output_path, index=False)
print(f"\n✓ Saved to {output_path}")

# Also save all receiver-team combinations for reference
all_targets_path = data_dir / "interim" / "all_receiver_targets.csv"
receiver_targets.sort_values(['possession_team', 'targets'], ascending=[True, False]).to_csv(
    all_targets_path, index=False
)
print(f"✓ Saved all receiver targets to {all_targets_path}")

print(f"\nTotal teams: {top_receiver_per_team['possession_team'].nunique()}")
print(f"Total unique receivers identified: {len(top_receiver_per_team)}")
