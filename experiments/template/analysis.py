"""
Experiment [NUMBER]: [TITLE]
Main analysis script
"""

import sys
from pathlib import Path
import yaml
import json
import logging
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parents[2]))

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

from src.data.loaders import load_data
from src.stats.hypothesis_tests import run_t_test
from src.visualization.distributions import plot_distribution_comparison
from src.utils.logging import setup_logger
from src.utils.reporting import generate_report


def load_config(config_path: str = "config.yaml") -> dict:
    """Load experiment configuration."""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def setup_directories(config: dict) -> None:
    """Create output directories if they don't exist."""
    Path(config['output']['results_dir']).mkdir(parents=True, exist_ok=True)
    Path(config['output']['figures_dir']).mkdir(parents=True, exist_ok=True)
    Path(config['output']['log_dir']).mkdir(parents=True, exist_ok=True)


def main():
    """Main analysis pipeline."""
    # Load configuration
    config = load_config()

    # Setup
    setup_directories(config)
    logger = setup_logger(
        log_dir=config['output']['log_dir'],
        experiment_name=config['experiment']['name']
    )

    logger.info(f"Starting experiment: {config['experiment']['name']}")

    # Load data
    # data = load_data(config['data']['raw_path'])

    # Perform analysis
    # results = ...

    # Generate visualizations
    # fig = plot_distribution_comparison(...)
    # plt.savefig(f"{config['output']['figures_dir']}/plot.png", dpi=config['visualization']['dpi'])

    # Save results
    results = {
        'experiment': config['experiment']['name'],
        'date': datetime.now().isoformat(),
        'results': {}
    }

    with open(f"{config['output']['results_dir']}/statistics.json", 'w') as f:
        json.dump(results, f, indent=2)

    logger.info("Analysis complete!")

    return results


if __name__ == "__main__":
    main()
