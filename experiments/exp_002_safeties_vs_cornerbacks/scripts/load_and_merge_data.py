"""
Data Loading and Merging Script
Loads all weekly input/output tracking data and merges with supplementary play data.
"""

import sys
from pathlib import Path
import yaml
import pandas as pd
import numpy as np
from glob import glob
from tqdm import tqdm

# Add src to path
sys.path.append(str(Path(__file__).parents[3]))

from src.utils.logging import setup_logger


def load_config(config_path: str = None) -> dict:
    """Load experiment configuration."""
    if config_path is None:
        # Get the script directory and construct path to config
        script_dir = Path(__file__).parent
        config_path = script_dir.parent / "config.yaml"

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def load_supplementary_data(config: dict, logger) -> pd.DataFrame:
    """
    Load and preprocess supplementary play-level data.

    Parameters
    ----------
    config : dict
        Experiment configuration
    logger : logging.Logger
        Logger instance

    Returns
    -------
    pd.DataFrame
        Supplementary data with cleaned columns
    """
    logger.info("Loading supplementary data...")
    supp_file = Path(config['data']['supplementary_file'])

    df = pd.read_csv(supp_file)
    logger.info(f"Loaded {len(df)} plays from supplementary data")

    # Clean column names (remove quotes)
    df.columns = df.columns.str.replace('"', '')

    # Convert game_id and play_id to appropriate types
    df['game_id'] = df['game_id'].astype(str)
    df['play_id'] = df['play_id'].astype(int)

    logger.info(f"Unique games: {df['game_id'].nunique()}")
    logger.info(f"Pass result distribution:\n{df['pass_result'].value_counts()}")

    return df


def load_weekly_input_data(config: dict, logger) -> pd.DataFrame:
    """
    Load all weekly input (pre-throw) tracking data.

    Parameters
    ----------
    config : dict
        Experiment configuration
    logger : logging.Logger
        Logger instance

    Returns
    -------
    pd.DataFrame
        Combined input tracking data
    """
    logger.info("Loading weekly input tracking data...")
    train_dir = Path(config['data']['train_dir'])
    pattern = config['data']['input_pattern']

    # Find all input files
    input_files = sorted(glob(str(train_dir / pattern)))

    # Filter out Zone.Identifier files
    input_files = [f for f in input_files if 'Zone.Identifier' not in f]

    logger.info(f"Found {len(input_files)} input files")

    # Load and combine all weeks
    dfs = []
    for file in tqdm(input_files, desc="Loading input files"):
        week_df = pd.read_csv(file)
        week_num = Path(file).stem.split('_')[-1]  # Extract week number
        week_df['week'] = week_num
        dfs.append(week_df)

    combined_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Combined input data: {len(combined_df)} rows")

    # Convert types
    combined_df['game_id'] = combined_df['game_id'].astype(str)
    combined_df['play_id'] = combined_df['play_id'].astype(int)
    combined_df['nfl_id'] = combined_df['nfl_id'].astype(int)
    combined_df['frame_id'] = combined_df['frame_id'].astype(int)

    logger.info(f"Unique plays: {combined_df[['game_id', 'play_id']].drop_duplicates().shape[0]}")
    logger.info(f"Unique players: {combined_df['nfl_id'].nunique()}")

    return combined_df


def load_weekly_output_data(config: dict, logger) -> pd.DataFrame:
    """
    Load all weekly output (post-throw) tracking data.

    Parameters
    ----------
    config : dict
        Experiment configuration
    logger : logging.Logger
        Logger instance

    Returns
    -------
    pd.DataFrame
        Combined output tracking data
    """
    logger.info("Loading weekly output tracking data...")
    train_dir = Path(config['data']['train_dir'])
    pattern = config['data']['output_pattern']

    # Find all output files
    output_files = sorted(glob(str(train_dir / pattern)))

    # Filter out Zone.Identifier files
    output_files = [f for f in output_files if 'Zone.Identifier' not in f]

    logger.info(f"Found {len(output_files)} output files")

    # Load and combine all weeks
    dfs = []
    for file in tqdm(output_files, desc="Loading output files"):
        week_df = pd.read_csv(file)
        week_num = Path(file).stem.split('_')[-1]  # Extract week number
        week_df['week'] = week_num
        dfs.append(week_df)

    combined_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Combined output data: {len(combined_df)} rows")

    # Convert types
    combined_df['game_id'] = combined_df['game_id'].astype(str)
    combined_df['play_id'] = combined_df['play_id'].astype(int)
    combined_df['nfl_id'] = combined_df['nfl_id'].astype(int)
    combined_df['frame_id'] = combined_df['frame_id'].astype(int)

    # Rename position columns to avoid conflicts with input data
    combined_df = combined_df.rename(columns={
        'x': 'x_post',
        'y': 'y_post'
    })

    return combined_df


def merge_tracking_data(input_df: pd.DataFrame, output_df: pd.DataFrame,
                        supp_df: pd.DataFrame, config: dict, logger) -> pd.DataFrame:
    """
    Merge input, output, and supplementary data.

    Parameters
    ----------
    input_df : pd.DataFrame
        Input tracking data
    output_df : pd.DataFrame
        Output tracking data
    supp_df : pd.DataFrame
        Supplementary play data
    config : dict
        Experiment configuration
    logger : logging.Logger
        Logger instance

    Returns
    -------
    pd.DataFrame
        Merged dataset
    """
    logger.info("Merging datasets...")

    # First, merge input with supplementary data
    logger.info("Merging input with supplementary data...")
    merged = input_df.merge(
        supp_df,
        on=['game_id', 'play_id'],
        how='left'
    )
    logger.info(f"After merging with supplementary: {len(merged)} rows")

    # Check for plays without supplementary data
    missing_supp = merged['pass_result'].isna().sum()
    if missing_supp > 0:
        logger.warning(f"{missing_supp} rows missing supplementary data")

    # Merge with output data
    logger.info("Merging with output data...")
    # Output data has frame_id that corresponds to post-throw frames
    # We need to join on game_id, play_id, nfl_id
    # For now, we'll keep them separate and add output as aggregated features later

    # Store output data aggregations per player per play
    output_agg = output_df.groupby(['game_id', 'play_id', 'nfl_id']).agg({
        'x_post': ['first', 'last', 'mean'],
        'y_post': ['first', 'last', 'mean'],
        'frame_id': 'count'
    }).reset_index()

    # Flatten column names
    output_agg.columns = ['game_id', 'play_id', 'nfl_id',
                          'x_post_first', 'x_post_last', 'x_post_mean',
                          'y_post_first', 'y_post_last', 'y_post_mean',
                          'num_post_frames']

    # Merge aggregated output data
    merged = merged.merge(
        output_agg,
        on=['game_id', 'play_id', 'nfl_id'],
        how='left'
    )

    logger.info(f"Final merged dataset: {len(merged)} rows")

    return merged


def filter_for_analysis(df: pd.DataFrame, config: dict, logger) -> pd.DataFrame:
    """
    Filter data for relevant plays and players.

    Parameters
    ----------
    df : pd.DataFrame
        Merged dataset
    config : dict
        Experiment configuration
    logger : logging.Logger
        Logger instance

    Returns
    -------
    pd.DataFrame
        Filtered dataset
    """
    logger.info("Filtering data for analysis...")
    initial_rows = len(df)

    # Filter for defensive players
    df = df[df['player_side'] == config['filters']['player_side']].copy()
    logger.info(f"After filtering for defense: {len(df)} rows ({len(df)/initial_rows*100:.1f}%)")

    # Filter for relevant positions (safeties and cornerbacks)
    all_positions = (
        config['filters']['safety_positions'] +
        config['filters']['cornerback_positions']
    )
    df = df[df['player_position'].isin(all_positions)].copy()
    logger.info(f"After filtering for DBs: {len(df)} rows ({len(df)/initial_rows*100:.1f}%)")

    # Create position group column
    df['position_group'] = df['player_position'].apply(
        lambda x: 'safeties' if x in config['filters']['safety_positions'] else 'cornerbacks'
    )

    logger.info(f"Position group distribution:\n{df['position_group'].value_counts()}")

    # Filter for relevant pass results (interceptions for primary analysis)
    primary_results = config['filters']['pass_results_primary']
    df_primary = df[df['pass_result'].isin(primary_results)].copy()

    logger.info(f"Plays with interceptions: {len(df_primary)} rows")
    logger.info(f"Unique interception plays: {df_primary[['game_id', 'play_id']].drop_duplicates().shape[0]}")

    return df_primary


def save_merged_data(df: pd.DataFrame, config: dict, logger) -> None:
    """
    Save merged data to interim directory.

    Parameters
    ----------
    df : pd.DataFrame
        Merged dataset
    config : dict
        Experiment configuration
    logger : logging.Logger
        Logger instance
    """
    output_path = Path(config['data']['merged_tracking_file'])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving merged data to {output_path}...")
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} rows")

    # Print summary statistics
    logger.info("\n" + "="*60)
    logger.info("MERGED DATA SUMMARY")
    logger.info("="*60)
    logger.info(f"Total rows: {len(df):,}")
    logger.info(f"Unique plays: {df[['game_id', 'play_id']].drop_duplicates().shape[0]:,}")
    logger.info(f"Unique players: {df['nfl_id'].nunique():,}")
    logger.info(f"\nPosition distribution:")
    logger.info(df['position_group'].value_counts())
    if 'week' in df.columns:
        logger.info(f"\nWeeks covered:")
        logger.info(df['week'].value_counts().sort_index())
    logger.info("="*60)


def main():
    """Main data loading and merging pipeline."""
    # Load configuration
    config = load_config()

    # Setup logging
    logger = setup_logger(
        log_dir=config['output']['log_dir'],
        experiment_name=config['experiment']['name'] + "_data_loading"
    )

    logger.info("="*60)
    logger.info("DATA LOADING AND MERGING PIPELINE")
    logger.info("="*60)

    try:
        # Load supplementary data
        supp_df = load_supplementary_data(config, logger)

        # Load input tracking data
        input_df = load_weekly_input_data(config, logger)

        # Load output tracking data
        output_df = load_weekly_output_data(config, logger)

        # Merge datasets
        merged_df = merge_tracking_data(input_df, output_df, supp_df, config, logger)

        # Filter for analysis
        filtered_df = filter_for_analysis(merged_df, config, logger)

        # Save merged data
        save_merged_data(filtered_df, config, logger)

        logger.info("Data loading and merging completed successfully!")

    except Exception as e:
        logger.error(f"Error during data loading: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
