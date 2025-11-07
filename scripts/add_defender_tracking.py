"""
Add defender tracking metrics to calculate true separation at throw moment.

This script:
1. Loads all tracking data (18 weeks)
2. For each targeted play, finds nearest defender at throw moment
3. Calculates separation distance and coverage metrics
4. Saves results to data/processed/defender_separation.csv

Author: Claude Code
Date: 2025-11-06
"""

import pandas as pd
import numpy as np
from pathlib import Path
import glob

# Paths
DATA_DIR = Path(__file__).parent.parent / 'data'
RAW_DIR = DATA_DIR / 'raw'
PROCESSED_DIR = DATA_DIR / 'processed'

def load_supplementary_data():
    """Load supplementary data with time_to_throw."""
    supp_path = RAW_DIR / 'supplementary_data.csv'
    df = pd.read_csv(supp_path)

    # Ensure time_to_throw exists
    if 'time_to_throw' not in df.columns:
        print("Warning: time_to_throw not found. Calculating from max_frame_id...")
        # This should have been added by add_time_to_throw.py
        # If not, we'll calculate it here

    return df

def load_all_tracking_data():
    """Load and concatenate all weekly tracking files."""
    print("Loading tracking data from 18 weeks...")

    tracking_files = sorted(glob.glob(str(RAW_DIR / 'train' / 'input_2023_w*.csv')))

    if not tracking_files:
        raise FileNotFoundError(f"No tracking files found in {RAW_DIR / 'train'}")

    print(f"Found {len(tracking_files)} tracking files")

    # Load in chunks to manage memory
    tracking_dfs = []
    for i, file in enumerate(tracking_files, 1):
        print(f"  Loading week {i}/18: {Path(file).name}")
        df = pd.read_csv(file)
        tracking_dfs.append(df)

    # Concatenate all weeks
    print("Concatenating all tracking data...")
    tracking_df = pd.concat(tracking_dfs, ignore_index=True)

    print(f"Total tracking records: {len(tracking_df):,}")
    return tracking_df

def find_nearest_defender(tracking_df, supp_df):
    """
    For each targeted play, find the nearest defender at throw moment.

    Strategy: For each play with a route (route_of_targeted_receiver not null),
    find the offensive player with the maximum displacement (likely the target).

    Returns DataFrame with columns:
    - game_id, play_id
    - receiver_nfl_id, receiver_name, receiver_position
    - receiver_x, receiver_y
    - nearest_defender_id, nearest_defender_position, nearest_defender_name
    - separation_at_throw (yards)
    - coverage_cushion (separation at snap)
    - separation_change (throw - snap)
    - defenders_within_3yd, defenders_within_5yd
    """
    print("\nCalculating defender separation metrics...")

    # Get targeted plays from supplementary data (plays with a route designation)
    targeted_plays = supp_df[
        supp_df['route_of_targeted_receiver'].notna() &
        (supp_df['route_of_targeted_receiver'] != '')
    ][['game_id', 'play_id', 'route_of_targeted_receiver']].copy()
    print(f"Processing {len(targeted_plays):,} targeted plays")

    results = []

    for idx, (game_id, play_id, route) in enumerate(targeted_plays.values, 1):
        if idx % 1000 == 0:
            print(f"  Processed {idx:,}/{len(targeted_plays):,} plays ({idx/len(targeted_plays)*100:.1f}%)")

        # Get this play's tracking data
        play_data = tracking_df[
            (tracking_df['game_id'] == game_id) &
            (tracking_df['play_id'] == play_id)
        ]

        if len(play_data) == 0:
            continue

        # Get throw frame (last frame)
        throw_frame_id = play_data['frame_id'].max()
        throw_frame = play_data[play_data['frame_id'] == throw_frame_id]

        # Get snap frame (first frame)
        snap_frame_id = play_data['frame_id'].min()
        snap_frame = play_data[play_data['frame_id'] == snap_frame_id]

        # Identify target receiver: offensive player with most displacement
        # (likely ran the targeted route)
        offensive_players = play_data[play_data['player_side'] == 'Offense']

        if len(offensive_players) == 0:
            continue

        # Calculate displacement for each offensive player
        player_displacements = []
        for nfl_id in offensive_players['nfl_id'].unique():
            player_frames = offensive_players[offensive_players['nfl_id'] == nfl_id].sort_values('frame_id')
            if len(player_frames) < 2:
                continue

            start_x, start_y = player_frames.iloc[0][['x', 'y']]
            end_x, end_y = player_frames.iloc[-1][['x', 'y']]
            displacement = np.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)

            # Filter to receivers and RBs (not QB, OL)
            position = player_frames.iloc[0]['player_position']
            if position in ['WR', 'TE', 'RB', 'FB']:
                player_displacements.append({
                    'nfl_id': nfl_id,
                    'displacement': displacement,
                    'position': position,
                    'name': player_frames.iloc[0]['player_name']
                })

        if len(player_displacements) == 0:
            continue

        # Get player with max displacement (likely the target)
        target_player = max(player_displacements, key=lambda x: x['displacement'])
        target_nfl_id = target_player['nfl_id']

        # Get target receiver at throw
        receiver_throw = throw_frame[throw_frame['nfl_id'] == target_nfl_id]
        if len(receiver_throw) == 0:
            continue
        receiver_throw = receiver_throw.iloc[0]
        receiver_x = receiver_throw['x']
        receiver_y = receiver_throw['y']

        # Get target receiver at snap
        receiver_snap = snap_frame[snap_frame['nfl_id'] == target_nfl_id]
        if len(receiver_snap) == 0:
            receiver_snap_x = receiver_snap_y = np.nan
        else:
            receiver_snap = receiver_snap.iloc[0]
            receiver_snap_x = receiver_snap['x']
            receiver_snap_y = receiver_snap['y']

        # Get all defenders at throw frame
        defenders_throw = throw_frame[throw_frame['player_side'] == 'Defense'].copy()

        if len(defenders_throw) == 0:
            continue

        # Calculate distance from receiver to each defender
        defenders_throw['distance_to_receiver'] = np.sqrt(
            (defenders_throw['x'] - receiver_x)**2 +
            (defenders_throw['y'] - receiver_y)**2
        )

        # Find nearest defender
        nearest_idx = defenders_throw['distance_to_receiver'].idxmin()
        nearest = defenders_throw.loc[nearest_idx]

        separation_at_throw = nearest['distance_to_receiver']

        # Count defenders within zones
        defenders_within_3yd = (defenders_throw['distance_to_receiver'] <= 3).sum()
        defenders_within_5yd = (defenders_throw['distance_to_receiver'] <= 5).sum()

        # Get coverage cushion (separation at snap)
        if not np.isnan(receiver_snap_x):
            defenders_snap = snap_frame[snap_frame['player_side'] == 'Defense'].copy()
            if len(defenders_snap) > 0:
                defenders_snap['distance_to_receiver'] = np.sqrt(
                    (defenders_snap['x'] - receiver_snap_x)**2 +
                    (defenders_snap['y'] - receiver_snap_y)**2
                )
                coverage_cushion = defenders_snap['distance_to_receiver'].min()
                separation_change = separation_at_throw - coverage_cushion
            else:
                coverage_cushion = np.nan
                separation_change = np.nan
        else:
            coverage_cushion = np.nan
            separation_change = np.nan

        results.append({
            'game_id': game_id,
            'play_id': play_id,
            'route': route,
            'receiver_nfl_id': target_nfl_id,
            'receiver_name': target_player['name'],
            'receiver_position': target_player['position'],
            'receiver_x': receiver_x,
            'receiver_y': receiver_y,
            'nearest_defender_id': nearest['nfl_id'],
            'nearest_defender_name': nearest['player_name'],
            'nearest_defender_position': nearest['player_position'],
            'separation_at_throw': separation_at_throw,
            'coverage_cushion': coverage_cushion,
            'separation_change': separation_change,
            'defenders_within_3yd': defenders_within_3yd,
            'defenders_within_5yd': defenders_within_5yd,
            'throw_frame_id': throw_frame_id,
        })

    print(f"  Completed all {len(results):,} plays")

    return pd.DataFrame(results)

def main():
    print("="*60)
    print("DEFENDER TRACKING AND SEPARATION CALCULATION")
    print("="*60)

    # Load supplementary data
    print("\n1. Loading supplementary data...")
    supp_df = load_supplementary_data()
    print(f"   Loaded {len(supp_df):,} plays")

    # Load all tracking data
    print("\n2. Loading tracking data...")
    tracking_df = load_all_tracking_data()

    # Calculate defender separation
    print("\n3. Calculating nearest defender separation...")
    separation_df = find_nearest_defender(tracking_df, supp_df)

    # Save results
    output_path = PROCESSED_DIR / 'defender_separation.csv'
    print(f"\n4. Saving results to {output_path}")
    separation_df.to_csv(output_path, index=False)

    # Summary statistics
    print("\n" + "="*60)
    print("SUMMARY STATISTICS")
    print("="*60)
    print(f"\nTotal plays with separation calculated: {len(separation_df):,}")
    print(f"\nSeparation at Throw (yards):")
    print(f"  Mean:   {separation_df['separation_at_throw'].mean():.2f}")
    print(f"  Median: {separation_df['separation_at_throw'].median():.2f}")
    print(f"  Std:    {separation_df['separation_at_throw'].std():.2f}")
    print(f"  Min:    {separation_df['separation_at_throw'].min():.2f}")
    print(f"  Max:    {separation_df['separation_at_throw'].max():.2f}")

    print(f"\nCoverage Cushion at Snap (yards):")
    print(f"  Mean:   {separation_df['coverage_cushion'].mean():.2f}")
    print(f"  Median: {separation_df['coverage_cushion'].median():.2f}")

    print(f"\nSeparation Change (throw - snap):")
    print(f"  Mean:   {separation_df['separation_change'].mean():.2f}")
    print(f"  Median: {separation_df['separation_change'].median():.2f}")

    print(f"\nDefenders Within Zones:")
    print(f"  Within 3 yards: {separation_df['defenders_within_3yd'].mean():.2f} avg")
    print(f"  Within 5 yards: {separation_df['defenders_within_5yd'].mean():.2f} avg")

    print(f"\nMost Common Nearest Defender Positions:")
    print(separation_df['nearest_defender_position'].value_counts().head(10))

    print("\n" + "="*60)
    print("COMPLETE")
    print("="*60)
    print(f"\nOutput file: {output_path}")

if __name__ == '__main__':
    main()
