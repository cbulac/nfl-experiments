#!/usr/bin/env python3
"""
Add time_to_throw attribute to supplementary_data.csv

Each frame represents 0.1 seconds, so time_to_throw = max_frame_id * 0.1
"""

import pandas as pd
from pathlib import Path
import glob

# Paths
project_root = Path(__file__).parent.parent
train_dir = project_root / "data" / "raw" / "train"
supp_path = project_root / "data" / "raw" / "supplementary_data.csv"
output_path = project_root / "data" / "interim" / "supplementary_data_enhanced.csv"

print("Loading all raw tracking files to get max frame_id per play...")

# Get all input files
input_files = sorted(glob.glob(str(train_dir / "input_2023_*.csv")))
print(f"Found {len(input_files)} input files")

# Read all files and get max frame_id per play
all_frames = []
for i, file_path in enumerate(input_files, 1):
    week = file_path.split('_')[-1].replace('.csv', '')
    print(f"  [{i}/{len(input_files)}] Reading {week}...")

    # Only need game_id, play_id, and frame_id
    df = pd.read_csv(file_path, usecols=['game_id', 'play_id', 'frame_id'])
    all_frames.append(df)

# Combine all tracking data
print("\nCombining all tracking data...")
tracking_df = pd.concat(all_frames, ignore_index=True)
print(f"Total tracking records: {len(tracking_df):,}")

# Get max frame_id per play
print("\nCalculating max frame_id per play...")
frames_per_play = tracking_df.groupby(['game_id', 'play_id'])['frame_id'].max().reset_index()
frames_per_play.columns = ['game_id', 'play_id', 'max_frame_id']

# Calculate time to throw (max_frame_id * 0.1 seconds)
frames_per_play['time_to_throw'] = frames_per_play['max_frame_id'] * 0.1

print(f"Calculated time_to_throw for {len(frames_per_play):,} plays")
print(f"\nTime to throw statistics:")
print(f"  Mean: {frames_per_play['time_to_throw'].mean():.2f} seconds")
print(f"  Median: {frames_per_play['time_to_throw'].median():.2f} seconds")
print(f"  Min: {frames_per_play['time_to_throw'].min():.2f} seconds")
print(f"  Max: {frames_per_play['time_to_throw'].max():.2f} seconds")
print(f"  Std: {frames_per_play['time_to_throw'].std():.2f} seconds")

# Load supplementary data
print("\nLoading supplementary data...")
supp_df = pd.read_csv(supp_path)
print(f"Loaded {len(supp_df):,} plays from supplementary data")

# Merge time_to_throw
print("\nMerging time_to_throw into supplementary data...")
enhanced_df = supp_df.merge(
    frames_per_play[['game_id', 'play_id', 'time_to_throw']],
    on=['game_id', 'play_id'],
    how='left'
)

# Check for missing values
missing_count = enhanced_df['time_to_throw'].isna().sum()
if missing_count > 0:
    print(f"\nWARNING: {missing_count} plays missing time_to_throw data")
else:
    print("\n✓ All plays have time_to_throw data")

# Verify column was added
print(f"\nOriginal columns: {len(supp_df.columns)}")
print(f"Enhanced columns: {len(enhanced_df.columns)}")
print(f"New column: time_to_throw")

# Save enhanced data
print(f"\nSaving enhanced supplementary data to {output_path}...")
enhanced_df.to_csv(output_path, index=False)
print(f"✓ Saved {len(enhanced_df):,} records with {len(enhanced_df.columns)} columns")

# Show sample
print("\nSample of enhanced data:")
print(enhanced_df[['game_id', 'play_id', 'play_description', 'time_to_throw']].head(10))

print("\n✓ Complete!")
print(f"\nEnhanced file location: {output_path}")
