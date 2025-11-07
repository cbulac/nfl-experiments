# Experiment 002: Safeties vs Cornerbacks in Interception Scenarios

**Date:** 2025-11-05
**Status:** Ready to Run
**Author:** Your Name

## Overview

This experiment performs a comprehensive comparative analysis of safeties (SS, FS, S) and cornerbacks (CB) in plays that result in interceptions. The analysis focuses on pre-throw positioning, movement patterns, speed, acceleration, and directional alignment to understand how these two position groups differ in their approach to interception opportunities.

## Research Questions

1. **Positioning**: Do safeties and cornerbacks differ in their distance from ball landing locations?
2. **Anticipation**: Which position group demonstrates better directional alignment to ball landing spots?
3. **Speed Compensation**: Do cornerbacks compensate for closer positioning with higher speed?
4. **Coverage Context**: How do different coverage schemes affect each position's effectiveness?
5. **Success Factors**: What features best predict interception success for each position?

## Hypothesis

See `hypothesis.md` for detailed hypothesis statements. Primary hypotheses include:

- **H1**: Safeties are positioned significantly farther from ball landing locations than cornerbacks
- **H2**: Safeties demonstrate better directional alignment to ball landing locations
- **H3**: Cornerbacks have higher average speed than safeties
- **H4**: Coverage scheme differentially affects position group involvement
- **H5**: Different features predict success for each position group

## Data Sources

### Input Data
- **Input Files**: `data/raw/train/input_2023_wXX.csv` (pre-throw tracking data)
  - Player position (x, y), speed (s), acceleration (a), direction (dir), orientation (o)
  - Frame-by-frame tracking before QB throw
  - Ball landing coordinates

- **Output Files**: `data/raw/train/output_2023_wXX.csv` (post-throw tracking data)
  - Player positions after QB throw
  - 21 frames of post-throw movement

- **Supplementary Data**: `data/raw/supplementary_data.csv`
  - Play outcomes (pass_result: "I" for interception)
  - Coverage schemes and play context
  - Game situation variables

## Methodology

### Pipeline Overview

```
1. Data Loading & Merging → 2. Feature Engineering → 3. Statistical Analysis → 4. Visualization
   (scripts/load_and_merge_data.py)  (scripts/engineer_features.py)     (analysis.py)
```

### Step-by-Step Execution

#### Step 1: Data Loading and Merging
```bash
cd experiments/exp_002_safeties_vs_cornerbacks
python scripts/load_and_merge_data.py
```

**What it does:**
- Loads all weekly input/output tracking files
- Merges with supplementary play-level data
- Filters for interception plays and defensive backs
- Creates unified tracking dataset
- Outputs: `data/interim/merged_tracking_data.csv`

#### Step 2: Feature Engineering
```bash
python scripts/engineer_features.py
```

**What it does:**
- Calculates spatial features (distance to ball, field position)
- Calculates kinematic features (speed, acceleration metrics)
- Calculates directional features (angle alignment, orientation)
- Calculates temporal features (closing rate, reaction time)
- Aggregates frame-level data to play-level
- Outputs: `data/interim/engineered_features.csv`

#### Step 3: Statistical Analysis
```bash
python analysis.py
```

**What it does:**
- Runs hypothesis tests (H1, H2, H3)
- Calculates effect sizes (Cohen's d)
- Checks statistical assumptions
- Generates comparison visualizations
- Outputs: `results/statistics.json`, figures in `results/figures/`

### All-in-One Execution

```bash
# Run complete pipeline
python scripts/load_and_merge_data.py && \
python scripts/engineer_features.py && \
python analysis.py
```

## Configuration

All experiment parameters are defined in `config.yaml`:

- **Data paths**: Input/output file locations
- **Filtering criteria**: Position groups, pass results
- **Feature engineering**: Which features to calculate and their parameters
- **Statistical tests**: Significance levels, test types
- **Visualization**: Plot styles, colors, figure sizes

Modify `config.yaml` to customize the analysis without changing code.

## Features Calculated

### Spatial Features
- `initial_dist_to_ball`: Distance to ball landing at first frame
- `min_dist_to_ball`: Minimum distance achieved during play
- `dist_from_los`: Distance from line of scrimmage
- `dist_from_center`: Distance from field center

### Kinematic Features
- `avg_speed`, `max_speed`, `min_speed`: Speed statistics
- `speed_at_throw`: Speed at moment of throw
- `avg_accel`, `max_accel`: Acceleration statistics

### Directional Features
- `angle_to_ball`: Angle from player to ball landing location
- `avg_dir_alignment`: Angular difference between movement direction and ball
- `avg_orient_alignment`: Angular difference between body orientation and ball
- `avg_body_control`: Difference between movement direction and orientation

### Temporal Features
- `avg_closing_rate`: Rate of distance reduction to ball
- `reaction_frame_min`: Estimated frame of reaction

### Post-Throw Features
- `post_throw_distance`: Total distance traveled post-throw
- `final_proximity_to_ball`: Final distance from ball
- `convergence_distance`: Distance closed toward ball

## Expected Results

Based on football domain knowledge:

| Hypothesis | Expected Result | Rationale |
|------------|----------------|-----------|
| H1: Positioning | ✓ Supported | Safeties play deeper by design |
| H2: Alignment | ? Uncertain | Could go either way |
| H3: Speed | ✓ Supported | CBs are typically faster players |
| H4: Coverage | ✓ Supported | Zone favors safeties, man favors CBs |
| H5: Predictors | ✓ Supported | Positions have different roles |

## Output Files

### Results
- `results/statistics.json`: Complete statistical test results
- `results/figures/distance_comparison.png`: Distance distribution comparison
- `results/figures/speed_comparison.png`: Speed distribution comparison
- `results/figures/alignment_comparison.png`: Directional alignment comparison

### Logs
- `logs/YYYY-MM-DD_HH-MM-SS_run.log`: Execution log with timestamps

## Interpretation Guide

### Effect Sizes (Cohen's d)
- **Small**: d = 0.2
- **Medium**: d = 0.5
- **Large**: d = 0.8

### Statistical Significance
- **α = 0.01** (Bonferroni corrected for 5 hypotheses)
- p-value < 0.01 → Reject null hypothesis
- p-value ≥ 0.01 → Fail to reject null hypothesis

### Practical Significance
Even if statistically significant, consider practical importance:
- Is the difference meaningful in real game situations?
- What is the magnitude of the effect?

## Dependencies

See root `requirements.txt` for all dependencies. Key packages:
- pandas, numpy: Data manipulation
- scipy, statsmodels: Statistical testing
- matplotlib, seaborn: Visualization
- pyyaml: Configuration management
- tqdm: Progress bars

## Troubleshooting

### Common Issues

**Issue**: `FileNotFoundError: Engineered features file not found`
- **Solution**: Run the pipeline in order (load → engineer → analyze)

**Issue**: Memory error during data loading
- **Solution**: Adjust `chunk_size` in `config.yaml` or process fewer weeks

**Issue**: No interception plays found
- **Solution**: Check that `supplementary_data.csv` contains plays with `pass_result == "I"`

**Issue**: Plots not displaying correctly
- **Solution**: Ensure matplotlib backend is properly configured

## Extending the Analysis

### Adding New Hypotheses

1. Define hypothesis in `hypothesis.md`
2. Add test function to `analysis.py`:
   ```python
   def test_h4_new_hypothesis(df, config, logger):
       # Your test logic
       return results
   ```
3. Call from `main()` and add to results dictionary
4. Update configuration in `config.yaml` if needed

### Adding New Features

1. Add feature calculation to appropriate function in `scripts/engineer_features.py`
2. Add feature name to relevant aggregation in `create_play_level_dataset()`
3. Update documentation

### Analyzing Subgroups

Modify filtering in `load_data()` to focus on specific:
- Coverage types (zone vs man)
- Pass distances (short vs deep)
- Game situations (score differential, quarter)

## References

- NFL Big Data Bowl documentation
- Player tracking data schema
- Statistical methods: Cohen's d, t-tests, chi-square tests

## Contact

For questions or issues with this experiment, contact [Your Name].

---

**Next Steps**: After running this experiment, consider:
1. Analyzing near-miss plays (incomplete passes where DBs were close)
2. Time-series analysis of player trajectories
3. Predictive modeling for interception probability
4. Coverage scheme deep-dive analysis
