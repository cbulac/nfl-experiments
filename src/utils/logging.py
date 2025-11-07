"""
Logging utilities for experiments.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional


def setup_logger(
    log_dir: str = "logs",
    experiment_name: str = "experiment",
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = True
) -> logging.Logger:
    """
    Set up logger for experiment tracking.

    Parameters
    ----------
    log_dir : str, default="logs"
        Directory for log files
    experiment_name : str, default="experiment"
        Name of the experiment
    level : int, default=logging.INFO
        Logging level
    log_to_file : bool, default=True
        Whether to log to file
    log_to_console : bool, default=True
        Whether to log to console

    Returns
    -------
    logging.Logger
        Configured logger instance

    Examples
    --------
    >>> logger = setup_logger(log_dir="logs", experiment_name="exp_001")
    >>> logger.info("Starting analysis...")
    """
    # Create logger
    logger = logging.getLogger(experiment_name)
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers = []

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler
    if log_to_file:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        file_handler = logging.FileHandler(
            Path(log_dir) / f"{timestamp}_run.log"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def log_experiment_info(
    logger: logging.Logger,
    config: dict
) -> None:
    """
    Log experiment configuration information.

    Parameters
    ----------
    logger : logging.Logger
        Logger instance
    config : dict
        Experiment configuration dictionary
    """
    logger.info("=" * 60)
    logger.info("EXPERIMENT CONFIGURATION")
    logger.info("=" * 60)

    for section, values in config.items():
        logger.info(f"\n{section.upper()}:")
        if isinstance(values, dict):
            for key, value in values.items():
                logger.info(f"  {key}: {value}")
        else:
            logger.info(f"  {values}")

    logger.info("=" * 60)


class ExperimentLogger:
    """
    Context manager for experiment logging.

    Examples
    --------
    >>> with ExperimentLogger("exp_001", log_dir="logs") as logger:
    ...     logger.info("Running analysis...")
    ...     # Your experiment code here
    """

    def __init__(
        self,
        experiment_name: str,
        log_dir: str = "logs",
        level: int = logging.INFO
    ):
        self.experiment_name = experiment_name
        self.log_dir = log_dir
        self.level = level
        self.logger = None
        self.start_time = None

    def __enter__(self):
        self.logger = setup_logger(
            log_dir=self.log_dir,
            experiment_name=self.experiment_name,
            level=self.level
        )
        self.start_time = datetime.now()
        self.logger.info(f"Starting experiment: {self.experiment_name}")
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.now()
        duration = end_time - self.start_time

        if exc_type is not None:
            self.logger.error(f"Experiment failed with error: {exc_val}")
        else:
            self.logger.info(f"Experiment completed successfully")

        self.logger.info(f"Total duration: {duration}")

        # Return False to propagate exceptions
        return False
