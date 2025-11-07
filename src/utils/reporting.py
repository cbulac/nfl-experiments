"""
Reporting utilities for experiment results.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd


def save_results(
    results: Dict[str, Any],
    output_path: str,
    format: str = 'json'
) -> None:
    """
    Save experiment results to file.

    Parameters
    ----------
    results : dict
        Results dictionary to save
    output_path : str
        Path to save results
    format : str, default='json'
        Output format: 'json' or 'csv'

    Examples
    --------
    >>> results = {'test_statistic': 2.5, 'p_value': 0.013}
    >>> save_results(results, 'results/statistics.json')
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if format == 'json':
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
    elif format == 'csv':
        df = pd.DataFrame([results])
        df.to_csv(output_path, index=False)
    else:
        raise ValueError(f"Unsupported format: {format}")


def load_results(
    input_path: str,
    format: str = 'json'
) -> Dict[str, Any]:
    """
    Load experiment results from file.

    Parameters
    ----------
    input_path : str
        Path to results file
    format : str, default='json'
        Input format: 'json' or 'csv'

    Returns
    -------
    dict
        Loaded results
    """
    if format == 'json':
        with open(input_path, 'r') as f:
            return json.load(f)
    elif format == 'csv':
        df = pd.read_csv(input_path)
        return df.to_dict('records')[0]
    else:
        raise ValueError(f"Unsupported format: {format}")


def generate_report(
    results: Dict[str, Any],
    config: Dict[str, Any],
    output_path: Optional[str] = None
) -> str:
    """
    Generate markdown report from results.

    Parameters
    ----------
    results : dict
        Experiment results
    config : dict
        Experiment configuration
    output_path : str, optional
        Path to save report. If None, returns string only.

    Returns
    -------
    str
        Markdown formatted report

    Examples
    --------
    >>> report = generate_report(results, config, 'results/report.md')
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    report_lines = [
        f"# Experiment Report: {config.get('experiment', {}).get('name', 'Unknown')}",
        "",
        f"**Generated:** {timestamp}",
        f"**Author:** {config.get('experiment', {}).get('author', 'Unknown')}",
        "",
        "## Configuration",
        "",
        "```yaml"
    ]

    # Add configuration
    import yaml
    report_lines.append(yaml.dump(config, default_flow_style=False))
    report_lines.append("```")
    report_lines.append("")

    # Add results
    report_lines.extend([
        "## Results",
        "",
        "### Statistical Test Results",
        ""
    ])

    if 'results' in results:
        for key, value in results['results'].items():
            report_lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")
    else:
        for key, value in results.items():
            if key not in ['experiment', 'date', 'status']:
                report_lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")

    report_lines.extend([
        "",
        "## Interpretation",
        "",
        "_Add interpretation of results here_",
        "",
        "## Conclusions",
        "",
        "_Add conclusions here_",
        "",
        "## Recommendations",
        "",
        "_Add recommendations for next steps_"
    ])

    report_text = "\n".join(report_lines)

    # Save if path provided
    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(report_text)

    return report_text


def compile_experiment_summary(
    experiments_dir: str = "experiments",
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Compile summary of all experiments.

    Parameters
    ----------
    experiments_dir : str, default="experiments"
        Directory containing experiment folders
    output_path : str, optional
        Path to save summary CSV

    Returns
    -------
    pd.DataFrame
        Summary DataFrame with all experiment results
    """
    experiments_path = Path(experiments_dir)
    summaries = []

    for exp_dir in experiments_path.iterdir():
        if exp_dir.is_dir() and exp_dir.name != 'template':
            results_file = exp_dir / 'results' / 'statistics.json'

            if results_file.exists():
                with open(results_file, 'r') as f:
                    results = json.load(f)
                    summaries.append({
                        'experiment': exp_dir.name,
                        **results
                    })

    df = pd.DataFrame(summaries)

    if output_path is not None:
        df.to_csv(output_path, index=False)

    return df
