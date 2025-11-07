# Experiment 004: Receiver Proximity Classification

**Date:** 2025-11-06
**Status:** Ready to Run
**Related Experiment:** exp_003_help_vs_primary_defenders

## Overview

This experiment tests the **same hypothesis** as Experiment 003, but uses a **different classification method** to identify primary vs. help defenders.

**Research Question:** Are help defenders more likely to intercept passes than primary defenders?

## Key Difference from Experiment 003

### Experiment 003 Classification
- **Primary Defender:** Closest defensive back to **BALL LANDING LOCATION** (at throw moment)
- **Rationale:** Assumes the closest defender to where the ball lands was likely the primary coverage
- **Timing:** Measured at the moment of QB throw

### Experiment 004 Classification (THIS EXPERIMENT)
- **Primary Defender:** Closest defensive back to **TARGET RECEIVER LOCATION** (at play start)
- **Rationale:** Represents initial coverage assignment before the play develops
- **Timing:** Measured at the first frame (play start)

## Methodology

### Classification Process

1. **Identify Target Receiver Location**
   - Use ball landing location as proxy for target receiver position
   - This is where the receiver was running their route

2. **Calculate Initial Distances**
   - For each defender, measure distance to target receiver location
   - Use **first frame** data (play start) for "initial assignment"
   - Formula: `distance = sqrt((x - target_x)² + (y - target_y)²)`

3. **Rank Defenders**
   - Within each play, rank all defenders by distance to target receiver
   - Rank 1 = closest defender (PRIMARY)
   - Rank 2+ = farther defenders (HELP)

4. **Assign Labels**
   - Rank 1 → `defender_type = "primary"`
   - Rank > 1 → `defender_type = "help"`

### Expected Differences

This classification should capture:
- **Initial coverage assignments** (who was supposed to cover that receiver)
- **Pre-snap positioning** (alignment before play starts)
- **Route-specific coverage** (man coverage on specific receiver)

Whereas exp_003 captured:
- **Final positioning** (who ended up closest when ball was thrown)
- **Coverage execution** (who successfully stayed with receiver)
- **Play development** (how coverage evolved during the play)

## Hypotheses

### H1: Interception Success Rate
- **Null:** No difference in INT rate between help and primary defenders
- **Alternative:** Help defenders have higher INT rate (one-tailed)
- **Test:** Chi-square test + Two-proportion z-test
- **Prediction:** Results may differ from exp_003 if initial assignment differs from final positioning

### H2: Receiver Proximity Validation
- **Null:** No difference in distance to target receiver at play start
- **Alternative:** Primary defenders are closer to receiver (one-tailed)
- **Test:** Independent t-test
- **Expected:** Primary should be significantly closer (validates classification)

## Data Pipeline

```
merged_tracking_data.csv (frame-level)
    ↓
Extract first frame positions
    ↓
Calculate distance to ball landing location (receiver proxy)
    ↓
Rank defenders by receiver proximity
    ↓
Merge with engineered_features.csv
    ↓
Classify as primary/help
    ↓
Statistical analysis
```

## Execution

### Run the Experiment

```bash
cd experiments/exp_004_receiver_proximity_classification
python analysis.py
```

**Runtime:** ~15 seconds (processes frame-level data)

### Output Files

**Results:**
- `results/statistics.json` - Statistical results with receiver proximity classification
- `results/receiver_proximity_classification.csv` - Processed data with classifications

**Visualizations:**
- `results/figures/interception_rates_by_defender_type.png` - INT rates comparison
- `results/figures/receiver_proximity_comparison.png` - Distance to receiver validation

**Logs:**
- `logs/YYYY-MM-DD_HH-MM-SS_run.log` - Detailed execution log

## Comparison with Experiment 003

After running both experiments, compare:

1. **Classification Agreement**
   - What % of defenders are classified the same in both experiments?
   - Which plays show largest divergence?

2. **Interception Rates**
   - Do results change with different classification?
   - Is proximity-to-receiver or proximity-to-ball more predictive?

3. **Distance Validation**
   - exp_003: Primary ~11.7 yards from ball, Help ~23.8 yards
   - exp_004: How do distances to receiver compare?

## Expected Scenarios

### Scenario A: Similar Results to exp_003
```
Primary: ~40% INT rate
Help: ~12% INT rate
```
**Interpretation:** Classification method doesn't matter much; proximity is proximity

### Scenario B: More Balanced Results
```
Primary: ~25% INT rate
Help: ~20% INT rate
```
**Interpretation:** Initial assignment differs from final positioning; play development matters

### Scenario C: Reversed Results
```
Primary: ~15% INT rate
Help: ~30% INT rate
```
**Interpretation:** Help defenders (not initially assigned) actually make more INTs

## Coaching Implications

### If Results Match exp_003:
- Both initial assignment and final positioning tell same story
- Proximity to receiver/ball is the dominant factor
- Coverage execution matters more than initial alignment

### If Results Differ:
- Initial assignment ≠ final positioning
- Play development and adjustment matter
- May reveal importance of "breaking on ball" vs "staying with receiver"
- Could inform zone vs man coverage strategy

## Limitations

1. **Receiver Proxy:** We use ball landing location as proxy for receiver position
   - True receiver position may differ slightly
   - Receiver may have adjusted route

2. **First Frame Timing:** "Play start" may not be exactly at snap
   - Some motion may have occurred
   - Pre-snap adjustments not captured

3. **Coverage Scheme Unknown:** Don't know if man or zone coverage on each play
   - Initial proximity may not indicate true assignment
   - Zone defenders may be "close" but not assigned

## Dependencies

- Python 3.8+
- pandas, numpy, scipy
- matplotlib, seaborn
- See root `requirements.txt`

## Reproducibility

- **Random seed:** 42
- **Data version:** Same as exp_003 (merged_tracking_data.csv + engineered_features.csv)
- **Environment:** Documented in `environment.yml`

---

**Key Question:** Does classifying primary defender by initial receiver proximity (vs. final ball proximity) change the interception rate findings?

*This experiment isolates the impact of classification method on the help vs. primary defender hypothesis.*
