### Project Description
Experiment template describing the structure of the repository to conduct experiments on data. 

### Directory Structure
experiment-template/
├── README.md                          # Project overview and setup instructions
├── requirements.txt                   # Python dependencies
├── .gitignore                        # Ignore data files, outputs, etc.
├── environment.yml                    # Conda environment (optional alternative)
│
├── data/                             # Data management
│   ├── raw/                          # Original, immutable data
│   ├── interim/                      # Intermediate, transformed data
│   ├── processed/                    # Final data for analysis
│   └── external/                     # Data from third parties
│
├── notebooks/                        # Jupyter notebooks for exploration
│   ├── 00_template.ipynb            # Template for new explorations
│   ├── 01_exploratory_analysis.ipynb
│   ├── 02_feature_investigation.ipynb
│   └── archived/                     # Old/completed explorations
│
├── experiments/                      # Formal hypothesis tests
│   ├── exp_001_description/         # One experiment per folder
│   │   ├── README.md                # Experiment documentation
│   │   ├── hypothesis.md            # Formal hypothesis statement
│   │   ├── config.yaml              # Experiment parameters
│   │   ├── analysis.py              # Main analysis script
│   │   ├── test_analysis.py         # Unit tests
│   │   ├── results/                 # Generated outputs
│   │   │   ├── statistics.json
│   │   │   ├── figures/
│   │   │   │   ├── distributions.png
│   │   │   │   └── comparison.png
│   │   │   └── report.md
│   │   └── logs/                    # Execution logs
│   │       └── 2024-11-05_run.log
│   │
│   │
│   └── template/                    # Template for new experiments
│       ├── README.md
│       ├── hypothesis.md
│       ├── config.yaml
│       └── analysis.py
│
├── src/                             # Reusable code (your toolkit)
│   ├── __init__.py
│   ├── data/                        # Data loading and preprocessing
│   │   ├── __init__.py
│   │   ├── loaders.py
│   │   ├── validators.py
│   │   └── transformers.py
│   ├── stats/                       # Statistical utilities
│   │   ├── __init__.py
│   │   ├── hypothesis_tests.py
│   │   ├── effect_sizes.py
│   │   └── assumptions.py
│   ├── visualization/               # Plotting utilities
│   │   ├── __init__.py
│   │   ├── distributions.py
│   │   └── comparisons.py
│   └── utils/                       # General utilities
│       ├── __init__.py
│       ├── logging.py
│       └── reporting.py
│
├── tests/                           # Unit tests for src/
│   ├── test_data_loaders.py
│   ├── test_statistics.py
│   └── test_validators.py
│
├── reports/                         # Cross-experiment summaries
│   └── executive_summary.pdf
│
└── scripts/                         # Utility scripts
    ├── create_experiment.sh         # Initialize new experiment
    ├── run_all_experiments.sh       # Batch execution
    └── generate_report.py           # Compile results
