"""
Feature Engineering Script
Calculates spatial, kinematic, directional, and temporal features from tracking data.
"""

import sys
from pathlib import Path
import yaml
import pandas as pd
import numpy as np
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


def calculate_distance(x1, y1, x2, y2):
    """Calculate Euclidean distance between two points."""
    return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)


def calculate_angle_to_target(x, y, target_x, target_y):
    """
    Calculate angle from current position to target.
    Returns angle in degrees (0-360).
    """
    dx = target_x - x
    dy = target_y - y
    angle_rad = np.arctan2(dy, dx)
    angle_deg = np.degrees(angle_rad)
    # Convert to 0-360 range
    angle_deg = (angle_deg + 360) % 360
    return angle_deg


def calculate_angular_difference(angle1, angle2):
    """
    Calculate smallest difference between two angles.
    Returns absolute difference in degrees (0-180).
    """
    diff = np.abs(angle1 - angle2)
    # Handle wrap-around
    diff = np.where(diff > 180, 360 - diff, diff)
    return diff


def engineer_spatial_features(df: pd.DataFrame, config: dict, logger) -> pd.DataFrame:
    """
    Calculate spatial features related to positioning.

    Parameters
    ----------
    df : pd.DataFrame
        Tracking data
    config : dict
        Configuration
    logger : logging.Logger
        Logger instance

    Returns
    -------
    pd.DataFrame
        Data with spatial features added
    """
    logger.info("Calculating spatial features...")

    # Distance to ball landing location
    df['dist_to_ball_landing'] = calculate_distance(
        df['x'], df['y'],
        df['ball_land_x'], df['ball_land_y']
    )

    # Distance from line of scrimmage
    df['dist_from_los'] = np.abs(df['x'] - df['absolute_yardline_number'])

    # Field position metrics
    field_width = config['features']['spatial']['field_width']
    hash_width = config['features']['spatial']['hash_width']

    df['dist_from_center'] = np.abs(df['y'] - field_width / 2)
    df['near_hash'] = (df['dist_from_center'] <= hash_width / 2).astype(int)
    df['near_sideline'] = ((df['y'] < 10) | (df['y'] > field_width - 10)).astype(int)

    logger.info("Spatial features calculated")

    return df


def engineer_kinematic_features(df: pd.DataFrame, config: dict, logger) -> pd.DataFrame:
    """
    Calculate kinematic features (speed, acceleration).

    These are aggregated per player per play.

    Parameters
    ----------
    df : pd.DataFrame
        Tracking data
    config : dict
        Configuration
    logger : logging.Logger
        Logger instance

    Returns
    -------
    pd.DataFrame
        Data with kinematic features added
    """
    logger.info("Calculating kinematic features...")

    # Group by play and player to get frame-level aggregations
    grouped = df.groupby(['game_id', 'play_id', 'nfl_id'])

    # Speed metrics
    speed_metrics = config['features']['kinematic']['speed_metrics']
    for metric in speed_metrics:
        if metric == 'mean':
            df['avg_speed'] = grouped['s'].transform('mean')
        elif metric == 'max':
            df['max_speed'] = grouped['s'].transform('max')
        elif metric == 'min':
            df['min_speed'] = grouped['s'].transform('min')
        elif metric == 'std':
            df['std_speed'] = grouped['s'].transform('std')

    # Acceleration metrics
    accel_metrics = config['features']['kinematic']['acceleration_metrics']
    for metric in accel_metrics:
        if metric == 'mean':
            df['avg_accel'] = grouped['a'].transform('mean')
        elif metric == 'max':
            df['max_accel'] = grouped['a'].transform('max')
        elif metric == 'std':
            df['std_accel'] = grouped['a'].transform('std')

    # Speed/acceleration at throw moment (last pre-throw frame)
    if config['features']['kinematic']['calculate_at_throw_moment']:
        last_frame = grouped['frame_id'].transform('max')
        df['speed_at_throw'] = np.where(
            df['frame_id'] == last_frame,
            df['s'],
            np.nan
        )
        df['accel_at_throw'] = np.where(
            df['frame_id'] == last_frame,
            df['a'],
            np.nan
        )

        # Forward fill within each group
        df['speed_at_throw'] = grouped['speed_at_throw'].transform(lambda x: x.fillna(method='bfill'))
        df['accel_at_throw'] = grouped['accel_at_throw'].transform(lambda x: x.fillna(method='bfill'))

    logger.info("Kinematic features calculated")

    return df


def engineer_directional_features(df: pd.DataFrame, config: dict, logger) -> pd.DataFrame:
    """
    Calculate directional and orientation features.

    Parameters
    ----------
    df : pd.DataFrame
        Tracking data
    config : dict
        Configuration
    logger : logging.Logger
        Logger instance

    Returns
    -------
    pd.DataFrame
        Data with directional features added
    """
    logger.info("Calculating directional features...")

    # Angle to ball landing location
    df['angle_to_ball'] = calculate_angle_to_target(
        df['x'], df['y'],
        df['ball_land_x'], df['ball_land_y']
    )

    # Direction alignment (how well is movement direction aligned with ball)
    df['dir_alignment'] = calculate_angular_difference(df['dir'], df['angle_to_ball'])

    # Orientation alignment (how well is body facing ball)
    df['orient_alignment'] = calculate_angular_difference(df['o'], df['angle_to_ball'])

    # Body control (difference between direction of movement and orientation)
    df['body_control'] = calculate_angular_difference(df['dir'], df['o'])

    # Aggregate per player per play
    grouped = df.groupby(['game_id', 'play_id', 'nfl_id'])

    df['avg_dir_alignment'] = grouped['dir_alignment'].transform('mean')
    df['avg_orient_alignment'] = grouped['orient_alignment'].transform('mean')
    df['avg_body_control'] = grouped['body_control'].transform('mean')

    # Good alignment indicator
    alignment_threshold = config['features']['directional']['alignment_threshold']
    df['good_dir_alignment'] = (df['dir_alignment'] < alignment_threshold).astype(int)
    df['pct_good_dir_alignment'] = grouped['good_dir_alignment'].transform('mean')

    logger.info("Directional features calculated")

    return df


def engineer_temporal_features(df: pd.DataFrame, config: dict, logger) -> pd.DataFrame:
    """
    Calculate temporal features (closing rate, reaction time).

    Parameters
    ----------
    df : pd.DataFrame
        Tracking data
    config : dict
        Configuration
    logger : logging.Logger
        Logger instance

    Returns
    -------
    pd.DataFrame
        Data with temporal features added
    """
    logger.info("Calculating temporal features...")

    # Sort by play and frame
    df = df.sort_values(['game_id', 'play_id', 'nfl_id', 'frame_id'])

    # Calculate change in distance to ball over time (closing rate)
    grouped = df.groupby(['game_id', 'play_id', 'nfl_id'])

    df['dist_change'] = grouped['dist_to_ball_landing'].diff()
    df['closing_rate'] = -df['dist_change']  # Negative distance change = closing

    # Average closing rate
    df['avg_closing_rate'] = grouped['closing_rate'].transform('mean')

    # Estimate reaction time (frame where player starts moving toward ball)
    # This is a simplified heuristic: when closing rate becomes consistently positive
    min_frames = config['features']['temporal']['min_frames_for_reaction']
    threshold = config['features']['temporal']['reaction_speed_threshold']

    # Rolling average of closing rate
    df['closing_rate_smooth'] = grouped['closing_rate'].transform(
        lambda x: x.rolling(window=min_frames, min_periods=1).mean()
    )

    # Frame where closing rate exceeds threshold
    df['reacting'] = (df['closing_rate_smooth'] > threshold).astype(int)
    df['reaction_frame'] = np.where(
        df['reacting'] == 1,
        df['frame_id'],
        np.nan
    )

    # Get earliest reaction frame per play
    df['reaction_frame_min'] = grouped['reaction_frame'].transform(lambda x: x.min())

    # Initial distance (at first frame)
    df['initial_dist_to_ball'] = grouped['dist_to_ball_landing'].transform('first')

    # Minimum distance achieved
    df['min_dist_to_ball'] = grouped['dist_to_ball_landing'].transform('min')

    logger.info("Temporal features calculated")

    return df


def engineer_post_throw_features(df: pd.DataFrame, config: dict, logger) -> pd.DataFrame:
    """
    Calculate features from post-throw movement.

    Parameters
    ----------
    df : pd.DataFrame
        Tracking data
    config : dict
        Configuration
    logger : logging.Logger
        Logger instance

    Returns
    -------
    pd.DataFrame
        Data with post-throw features added
    """
    logger.info("Calculating post-throw features...")

    # Total distance traveled post-throw
    # Approximate using straight-line distance from first to last post-throw position
    if 'x_post_first' in df.columns and 'x_post_last' in df.columns:
        df['post_throw_distance'] = calculate_distance(
            df['x_post_first'], df['y_post_first'],
            df['x_post_last'], df['y_post_last']
        )

        # Final proximity to ball
        df['final_proximity_to_ball'] = calculate_distance(
            df['x_post_last'], df['y_post_last'],
            df['ball_land_x'], df['ball_land_y']
        )

        # Initial proximity (at start of post-throw)
        df['initial_post_proximity_to_ball'] = calculate_distance(
            df['x_post_first'], df['y_post_first'],
            df['ball_land_x'], df['ball_land_y']
        )

        # Convergence rate
        df['convergence_distance'] = df['initial_post_proximity_to_ball'] - df['final_proximity_to_ball']

        logger.info("Post-throw features calculated")
    else:
        logger.warning("Post-throw position data not available")

    return df


def create_play_level_dataset(df: pd.DataFrame, config: dict, logger) -> pd.DataFrame:
    """
    Aggregate frame-level data to play level (one row per player per play).

    Parameters
    ----------
    df : pd.DataFrame
        Tracking data with engineered features
    config : dict
        Configuration
    logger : logging.Logger
        Logger instance

    Returns
    -------
    pd.DataFrame
        Play-level dataset
    """
    logger.info("Creating play-level dataset...")

    # Define columns to keep (take first value for identifiers)
    id_cols = ['game_id', 'play_id', 'nfl_id', 'player_name', 'player_position',
               'position_group', 'player_height', 'player_weight', 'player_birth_date']

    # Play context columns
    context_cols = ['week', 'pass_result', 'pass_length', 'pass_location_type',
                    'team_coverage_type', 'team_coverage_man_zone',
                    'down', 'yards_to_go', 'quarter',
                    'ball_land_x', 'ball_land_y', 'absolute_yardline_number']

    # Engineered feature columns (already aggregated)
    feature_cols = [
        'initial_dist_to_ball', 'min_dist_to_ball',
        'avg_speed', 'max_speed', 'min_speed', 'std_speed',
        'speed_at_throw', 'accel_at_throw',
        'avg_accel', 'max_accel', 'std_accel',
        'avg_dir_alignment', 'avg_orient_alignment', 'avg_body_control',
        'pct_good_dir_alignment',
        'avg_closing_rate', 'reaction_frame_min',
        'post_throw_distance', 'final_proximity_to_ball',
        'convergence_distance', 'num_post_frames'
    ]

    # Check which columns exist
    available_feature_cols = [col for col in feature_cols if col in df.columns]
    available_context_cols = [col for col in context_cols if col in df.columns]

    # Group and take first value for each play/player combination
    agg_dict = {}

    for col in id_cols + available_context_cols + available_feature_cols:
        if col in df.columns:
            agg_dict[col] = 'first'

    play_level_df = df.groupby(['game_id', 'play_id', 'nfl_id']).agg(agg_dict).reset_index(drop=True)

    logger.info(f"Created play-level dataset: {len(play_level_df)} rows")
    logger.info(f"Unique plays: {play_level_df[['game_id', 'play_id']].drop_duplicates().shape[0]}")
    logger.info(f"Unique players: {play_level_df['nfl_id'].nunique()}")

    return play_level_df


def save_engineered_data(df: pd.DataFrame, config: dict, logger) -> None:
    """
    Save engineered features dataset.

    Parameters
    ----------
    df : pd.DataFrame
        Engineered dataset
    config : dict
        Configuration
    logger : logging.Logger
        Logger instance
    """
    output_path = Path(config['data']['engineered_features_file'])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving engineered features to {output_path}...")
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} rows with {len(df.columns)} columns")

    # Print feature summary
    logger.info("\n" + "="*60)
    logger.info("FEATURE ENGINEERING SUMMARY")
    logger.info("="*60)
    logger.info(f"Total rows: {len(df):,}")
    logger.info(f"Total columns: {len(df.columns)}")
    logger.info(f"\nSample feature statistics:")

    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in ['initial_dist_to_ball', 'avg_speed', 'avg_dir_alignment'][:3]:
        if col in numeric_cols:
            logger.info(f"\n{col}:")
            logger.info(f"  Mean: {df[col].mean():.2f}")
            logger.info(f"  Std: {df[col].std():.2f}")
            logger.info(f"  Min: {df[col].min():.2f}")
            logger.info(f"  Max: {df[col].max():.2f}")

    logger.info("="*60)


def main():
    """Main feature engineering pipeline."""
    # Load configuration
    config = load_config()

    # Setup logging
    logger = setup_logger(
        log_dir=config['output']['log_dir'],
        experiment_name=config['experiment']['name'] + "_feature_engineering"
    )

    logger.info("="*60)
    logger.info("FEATURE ENGINEERING PIPELINE")
    logger.info("="*60)

    try:
        # Load merged data
        input_path = Path(config['data']['merged_tracking_file'])
        logger.info(f"Loading merged data from {input_path}...")
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} rows")

        # Engineer features
        df = engineer_spatial_features(df, config, logger)
        df = engineer_kinematic_features(df, config, logger)
        df = engineer_directional_features(df, config, logger)
        df = engineer_temporal_features(df, config, logger)
        df = engineer_post_throw_features(df, config, logger)

        # Create play-level dataset
        play_level_df = create_play_level_dataset(df, config, logger)

        # Save engineered data
        save_engineered_data(play_level_df, config, logger)

        logger.info("Feature engineering completed successfully!")

    except Exception as e:
        logger.error(f"Error during feature engineering: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
