#!/usr/bin/env python3
"""
Script to compile results from all experiments into a summary report.
"""

import sys
from pathlib import Path
import argparse
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.reporting import compile_experiment_summary, generate_report, load_results


def main():
    """Generate comprehensive report from all experiments."""
    parser = argparse.ArgumentParser(
        description='Generate summary report from all experiments'
    )
    parser.add_argument(
        '--experiments-dir',
        type=str,
        default='experiments',
        help='Directory containing experiments (default: experiments)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='reports/experiment_summary.csv',
        help='Output path for summary CSV (default: reports/experiment_summary.csv)'
    )
    parser.add_argument(
        '--format',
        type=str,
        choices=['csv', 'markdown', 'both'],
        default='both',
        help='Output format (default: both)'
    )

    args = parser.parse_args()

    print("Compiling experiment results...")
    print(f"Experiments directory: {args.experiments_dir}")
    print()

    # Compile summary
    try:
        summary_df = compile_experiment_summary(
            experiments_dir=args.experiments_dir
        )

        if len(summary_df) == 0:
            print("No experiment results found!")
            return

        print(f"Found {len(summary_df)} experiments with results")
        print()

        # Save CSV if requested
        if args.format in ['csv', 'both']:
            csv_output = Path(args.output)
            csv_output.parent.mkdir(parents=True, exist_ok=True)
            summary_df.to_csv(csv_output, index=False)
            print(f"✓ CSV summary saved to: {csv_output}")

        # Generate markdown report if requested
        if args.format in ['markdown', 'both']:
            md_output = Path(args.output).with_suffix('.md')
            generate_markdown_summary(summary_df, md_output)
            print(f"✓ Markdown report saved to: {md_output}")

        # Print summary to console
        print()
        print("=" * 70)
        print("EXPERIMENT SUMMARY")
        print("=" * 70)
        print(summary_df.to_string(index=False))
        print("=" * 70)

    except Exception as e:
        print(f"Error generating report: {e}")
        sys.exit(1)


def generate_markdown_summary(df, output_path):
    """
    Generate markdown formatted summary report.

    Parameters
    ----------
    df : pd.DataFrame
        Summary DataFrame
    output_path : Path
        Output file path
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    lines = [
        "# Experiment Summary Report",
        "",
        f"**Generated:** {timestamp}",
        f"**Total Experiments:** {len(df)}",
        "",
        "## Overview",
        "",
        df.to_markdown(index=False),
        "",
        "## Experiment Details",
        ""
    ]

    # Add individual experiment sections
    for _, row in df.iterrows():
        exp_name = row['experiment']
        lines.append(f"### {exp_name}")
        lines.append("")

        # Add key results
        for col in df.columns:
            if col != 'experiment':
                value = row[col]
                if value is not None and str(value) != 'nan':
                    lines.append(f"- **{col}:** {value}")

        lines.append("")

    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))


if __name__ == "__main__":
    main()
