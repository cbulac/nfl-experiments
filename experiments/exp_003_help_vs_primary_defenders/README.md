# Experiment 003: Help Defenders vs Primary Defenders in Interceptions

**Date:** 2025-11-06
**Status:** Ready to Run
**Author:** Your Name

## Overview

This experiment tests a fundamental defensive football concept: **Are help defenders more likely to intercept passes than primary defenders?**

Help defenders (providing secondary coverage) may have advantages in reading the QB, timing their break, and achieving better angles to the ball. Primary defenders (assigned to the targeted receiver) are closer but may be physically engaged with receivers.

## Research Question

**Primary Hypothesis:** Help defenders have a significantly higher interception success rate than primary defenders on plays that result in interceptions.

## Hypotheses

### H1: Interception Success Rate (**PRIMARY**)
- **Null:** No difference in INT rate between help and primary defenders
- **Alternative:** Help defenders have higher INT rate (one-tailed)
- **Test:** Chi-square test + Two-proportion z-test
- **Expected:** Help defenders show 1.5-2.0x higher success rate

### H2: Proximity Validation
- **Null:** No difference in distance to ball
- **Alternative:** Primary defenders are closer to ball (one-tailed)
- **Test:** Independent t-test
- **Expected:** Primary ~5-10 yards closer (validates classification)

### H3: Speed Among Successful Interceptors
- **Null:** No speed difference among players who intercepted
- **Alternative:** Help defenders who intercept are faster (two-tailed)
- **Test:** Independent t-test on successful INT only

### H4: Angle Advantage
- **Null:** No alignment difference among successful interceptors
- **Alternative:** Help defenders have better angles (one-tailed)
- **Test:** Independent t-test on `avg_dir_alignment`

### H5: Position Group Interaction
- **Null:** Help advantage doesn't differ by position (CB vs S)
- **Alternative:** Interaction effect exists
- **Test:** Logistic regression with interaction term

## Methodology

### Defining Defender Types

**Primary Defender:**
- Closest defensive back to ball landing location at throw moment
- Operationalized as: `rank(initial_dist_to_ball) == 1` per play
- Typically the player assigned to cover the targeted receiver

**Help Defender:**
- Any other defensive back on the play
- Operationalized as: `rank(initial_dist_to_ball) > 1` per play
- Providing secondary support, reading QB, positioned to help

### Identifying Interceptions

**Made Interception:**
- Player with minimum `final_proximity_to_ball` on each play
- Assumed to be the player who made the INT
- Binary outcome: 1 = made INT, 0 = did not

### Data Source

- Uses engineered features from **Experiment 002**
- Input: `data/interim/engineered_features.csv`
- 19,813 observations across 4,032 interception plays
- All features already calculated (distance, speed, alignment, etc.)

## Expected Results

### Scenario A: Help Defenders Advantage (Hypothesis Supported)
```
Primary Defender INT Rate: 15-20%
Help Defender INT Rate:    25-30%
Odds Ratio:                1.5-2.0
```
**Interpretation:** Help defenders benefit from better angles, QB reads, and timing

### Scenario B: Primary Defenders Advantage (Hypothesis Contradicted)
```
Primary Defender INT Rate: 30-40%
Help Defender INT Rate:    10-15%
Odds Ratio:                0.3-0.5
```
**Interpretation:** Proximity dominates; closest player has best opportunity

### Scenario C: No Difference (Null Hypothesis)
```
Both ~20% INT rate
Odds Ratio: ~1.0
```
**Interpretation:** Role doesn't matter; situation and skill dominate

## Execution

### Prerequisites
- Experiment 002 must be completed first
- Engineered features file must exist at: `data/interim/engineered_features.csv`

### Run the Experiment

```bash
cd experiments/exp_003_help_vs_primary_defenders
python analysis.py
```

**Runtime:** ~10 seconds

### Output Files

**Results:**
- `results/statistics.json` - Complete statistical results
- `results/help_vs_primary_defenders.csv` - Processed data with classifications

**Visualizations:**
- `results/figures/interception_rates_by_defender_type.png` - Bar chart of INT rates
- `results/figures/proximity_comparison.png` - Box plots of distance to ball
- `results/figures/speed_comparison_successful_ints.png` - Speed among interceptors
- `results/figures/angle_comparison_successful_ints.png` - Alignment among interceptors

**Logs:**
- `logs/YYYY-MM-DD_HH-MM-SS_run.log` - Detailed execution log

## Key Metrics

### Primary Outcome
- **Interception Rate:** Proportion of defenders who made INT
- **Odds Ratio:** Odds of INT for help vs. primary defenders
- **Relative Risk:** Risk ratio of INT for help vs. primary

### Validation Metrics
- **Distance to Ball:** Confirms primary are closer (validates classification)
- **Sample Sizes:** Ensures adequate power for detection
- **Effect Sizes:** Cohen's d for continuous measures

### Control Variables
- Position group (CB vs. Safety)
- Coverage type (Man vs. Zone)
- Pass length (Short, Medium, Deep)
- Down and distance
- Player speed

## Statistical Approach

### Primary Analysis
1. **Contingency Table:** [Defender Type × Made INT]
2. **Chi-Square Test:** Overall association
3. **Two-Proportion Z-Test:** One-tailed test of rates
4. **Odds Ratio:** With 95% confidence intervals

### Secondary Analyses
- **t-tests:** Compare continuous metrics (distance, speed, alignment)
- **Effect Sizes:** Cohen's d for magnitude interpretation
- **Logistic Regression:** Control for confounders
- **Stratification:** Separate by position group, coverage type

### Significance Levels
- **α = 0.05** (standard)
- **Bonferroni correction** if multiple comparisons
- **Power:** Extremely high (n > 19,000)

## Interpretation Guidelines

### Odds Ratio Interpretation
- **OR = 1.0:** No effect
- **OR = 1.5:** 50% higher odds for help defenders
- **OR = 2.0:** Double the odds for help defenders
- **OR = 3.0:** Triple the odds for help defenders
- **OR < 1.0:** Primary defenders have advantage

### Statistical Significance
- **p < 0.001:** Very strong evidence
- **p < 0.01:** Strong evidence
- **p < 0.05:** Moderate evidence (threshold)
- **p ≥ 0.05:** Insufficient evidence

### Effect Size (Cohen's d)
- **d = 0.2:** Small effect
- **d = 0.5:** Medium effect
- **d = 0.8:** Large effect

## Coaching Implications

### If Help Defenders Have Advantage:
- **Defensive Strategy:**
  - Emphasize help defense concepts
  - Train safeties to read QB eyes
  - Teach angles and ball tracking
  - Zone coverage may generate more INTs

- **Personnel:**
  - Value "ball hawk" skills in help defenders
  - Range and anticipation over pure speed
  - Deep safety positioning matters

### If Primary Defenders Have Advantage:
- **Defensive Strategy:**
  - Tight coverage on receivers is key
  - Man coverage may generate more INTs
  - Contest every throw at catch point
  - Proximity matters most

- **Personnel:**
  - Value press coverage ability
  - Physicality and receiver disruption
  - Man-to-man coverage skills

### If No Difference:
- **Interpretation:**
  - Interceptions are opportunistic
  - Individual player skill dominates
  - Scheme matters less than execution
  - Training should focus on fundamentals

## Limitations

1. **Role Inference:** Defender types inferred from proximity, not true assignments
2. **Selection Bias:** Only interception plays analyzed (not all pass attempts)
3. **Causality:** Association doesn't prove role causes INT success
4. **Scheme Variation:** Different teams use different defensive philosophies
5. **Player Quality:** Not controlling for individual skill levels
6. **Sample:** Limited to 2023 season data

## Extensions

### Future Analyses
1. **All Pass Plays:** Include non-interception passes for complete picture
2. **Near-Interceptions:** Analyze plays with passes defensed (PD)
3. **Coverage Specific:** Separate analysis for man vs. zone
4. **Player Level:** Individual defender performance tracking
5. **Temporal:** How positioning changes frame-by-frame pre-throw
6. **Bracket Coverage:** Special case with 2 primary defenders

### Additional Hypotheses
- Do help defenders intercept more on deep passes?
- Does the advantage differ between CBs and safeties?
- Do help defenders show better closing speed?
- Are help defender INTs more likely in zone coverage?

## Configuration

All parameters can be modified in `config.yaml`:

```yaml
# Defender classification method
defender_classification:
  method: "proximity_rank"  # or "distance_threshold"
  proximity_rank:
    primary_rank: 1  # Closest player

# Statistical tests
analysis:
  statistical_tests:
    alpha: 0.05
  h1_interception_rate:
    test_type: "chi_square"
    alternative: "greater"
```

## Dependencies

- Python 3.8+
- pandas, numpy, scipy
- matplotlib, seaborn
- See root `requirements.txt`

## Reproducibility

- **Random seed:** 42 (for any stochastic operations)
- **Data version:** Experiment 002 engineered features
- **Environment:** Documented in `environment.yml`

## References

- **Previous Experiment:** exp_002_safeties_vs_cornerbacks
- **Data Source:** NFL Big Data Bowl tracking data
- **Statistical Methods:** Chi-square, proportion tests, logistic regression

---

**Expected Runtime:** 10 seconds
**Expected Output:** 2-3 visualizations, JSON results, processed CSV
**Key Question:** Do help defenders intercept more than primary defenders?

*This experiment tests whether defensive football's "help defense" concept translates to measurable interception success advantages using objective tracking data.*
