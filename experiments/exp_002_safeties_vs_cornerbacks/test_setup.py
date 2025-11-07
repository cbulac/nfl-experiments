"""
Setup Test Script
Verifies that all required files and dependencies are in place before running the experiment.
"""

import sys
from pathlib import Path
import importlib.util

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'


def check_file_exists(file_path: Path, description: str) -> bool:
    """Check if a file exists."""
    if file_path.exists():
        print(f"{GREEN}✓{RESET} {description}: {file_path}")
        return True
    else:
        print(f"{RED}✗{RESET} {description}: {file_path} (NOT FOUND)")
        return False


def check_directory_exists(dir_path: Path, description: str) -> bool:
    """Check if a directory exists."""
    if dir_path.exists() and dir_path.is_dir():
        print(f"{GREEN}✓{RESET} {description}: {dir_path}")
        return True
    else:
        print(f"{RED}✗{RESET} {description}: {dir_path} (NOT FOUND)")
        return False


def check_module_import(module_name: str) -> bool:
    """Check if a Python module can be imported."""
    try:
        importlib.import_module(module_name)
        print(f"{GREEN}✓{RESET} Module: {module_name}")
        return True
    except ImportError:
        print(f"{RED}✗{RESET} Module: {module_name} (NOT INSTALLED)")
        return False


def main():
    """Run all setup checks."""
    print("="*60)
    print("EXPERIMENT SETUP VERIFICATION")
    print("="*60)

    all_checks_passed = True

    # Check experiment files
    print("\n1. Checking experiment files...")
    exp_dir = Path(".")
    checks = [
        (exp_dir / "config.yaml", "Configuration file"),
        (exp_dir / "hypothesis.md", "Hypothesis document"),
        (exp_dir / "README.md", "README file"),
        (exp_dir / "analysis.py", "Analysis script"),
        (exp_dir / "scripts/load_and_merge_data.py", "Data loading script"),
        (exp_dir / "scripts/engineer_features.py", "Feature engineering script"),
    ]

    for file_path, description in checks:
        if not check_file_exists(file_path, description):
            all_checks_passed = False

    # Check data directories
    print("\n2. Checking data directories...")
    data_checks = [
        (Path("../../data/raw/"), "Raw data directory"),
        (Path("../../data/raw/train/"), "Training data directory"),
    ]

    for dir_path, description in data_checks:
        if not check_directory_exists(dir_path, description):
            all_checks_passed = False

    # Check for data files
    print("\n3. Checking data files...")
    supp_data = Path("../../data/raw/supplementary_data.csv")
    if check_file_exists(supp_data, "Supplementary data"):
        # Check for at least one input/output file
        train_dir = Path("../../data/raw/train/")
        input_files = list(train_dir.glob("input_2023_*.csv"))
        output_files = list(train_dir.glob("output_2023_*.csv"))

        # Filter out Zone.Identifier files
        input_files = [f for f in input_files if 'Zone.Identifier' not in f.name]
        output_files = [f for f in output_files if 'Zone.Identifier' not in f.name]

        if input_files:
            print(f"{GREEN}✓{RESET} Found {len(input_files)} input files")
        else:
            print(f"{RED}✗{RESET} No input files found in {train_dir}")
            all_checks_passed = False

        if output_files:
            print(f"{GREEN}✓{RESET} Found {len(output_files)} output files")
        else:
            print(f"{RED}✗{RESET} No output files found in {train_dir}")
            all_checks_passed = False
    else:
        all_checks_passed = False

    # Check Python dependencies
    print("\n4. Checking Python dependencies...")
    required_modules = [
        'pandas',
        'numpy',
        'scipy',
        'matplotlib',
        'seaborn',
        'yaml',
        'tqdm'
    ]

    for module in required_modules:
        if not check_module_import(module):
            all_checks_passed = False

    # Check src modules
    print("\n5. Checking src modules...")
    sys.path.append(str(Path(__file__).parents[2]))

    src_modules = [
        'src.stats.hypothesis_tests',
        'src.stats.effect_sizes',
        'src.stats.assumptions',
        'src.visualization.distributions',
        'src.visualization.comparisons',
        'src.utils.logging',
        'src.utils.reporting'
    ]

    for module in src_modules:
        if not check_module_import(module):
            all_checks_passed = False

    # Check output directories
    print("\n6. Checking output directories...")
    output_dirs = [
        (exp_dir / "results", "Results directory"),
        (exp_dir / "results/figures", "Figures directory"),
        (exp_dir / "logs", "Logs directory"),
    ]

    for dir_path, description in output_dirs:
        if not check_directory_exists(dir_path, description):
            print(f"{YELLOW}  Creating {dir_path}...{RESET}")
            dir_path.mkdir(parents=True, exist_ok=True)

    # Final summary
    print("\n" + "="*60)
    if all_checks_passed:
        print(f"{GREEN}✓ ALL CHECKS PASSED{RESET}")
        print("\nYou're ready to run the experiment!")
        print("\nNext steps:")
        print("  1. python scripts/load_and_merge_data.py")
        print("  2. python scripts/engineer_features.py")
        print("  3. python analysis.py")
    else:
        print(f"{RED}✗ SOME CHECKS FAILED{RESET}")
        print("\nPlease fix the issues above before running the experiment.")
        print("\nCommon fixes:")
        print("  - Install missing packages: pip install -r ../../requirements.txt")
        print("  - Ensure data files are in ../../data/raw/")
        print("  - Check that you're in the experiment directory")

    print("="*60)

    return 0 if all_checks_passed else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
