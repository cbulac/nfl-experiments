# Analysis Strategy: Comparing Safeties and Cornerbacks in Interception Scenarios

**Date:** 2025-11-05
**Objective:** Compare safeties (SS, FS, S) and cornerbacks (CB) performance in interception scenarios, analyzing their pre-throw positioning/movement and post-throw outcomes.

---

## Data Understanding

### Available Data Files

1. **Input Files** (`input_2023_wXX.csv`): Player tracking data BEFORE QB throw
   - Columns: game_id, play_id, player_to_predict, nfl_id, frame_id, play_direction, absolute_yardline_number, player_name, player_height, player_weight, player_birth_date, player_position, player_side, player_role, x, y, s, a, dir, o, num_frames_output, ball_land_x, ball_land_y
   - Key metrics: position (x, y), speed (s), acceleration (a), direction (dir), orientation (o)
   - Time-series data: Multiple frames per play (frame_id)
   - Ball landing: ball_land_x, ball_land_y

2. **Output Files** (`output_2023_wXX.csv`): Player positioning AFTER QB throw
   - Columns: game_id, play_id, nfl_id, frame_id, x, y
   - Position tracking post-throw (21 frames based on num_frames_output)

3. **Supplementary Data** (`supplementary_data.csv`): Play-level metadata
   - Play outcome (pass_result: "I" = Interception, "C" = Complete, "IN" = Incomplete)
   - Coverage scheme (team_coverage_type, team_coverage_man_zone)
   - Pass characteristics (pass_length, pass_location_type)
   - Game context (score, quarter, down, distance)

### Relevant Player Positions
- **Safeties:** SS (Strong Safety), FS (Free Safety), S (Safety)
- **Cornerbacks:** CB (Cornerback)

---

## Data Processing Strategy

### Phase 1: Data Integration and Filtering

#### 1.1 Merge Input and Output Data
```python
# For each week:
# - Join input and output files on (game_id, play_id, nfl_id)
# - Separate pre-throw frames (input) and post-throw frames (output)
# - Create complete player trajectory dataset
```

#### 1.2 Link Supplementary Data
```python
# Join supplementary data on (game_id, play_id)
# Filter for relevant pass_result values:
# - Focus on "I" (Interceptions) for primary analysis
# - Include "C" and "IN" for comparison of "near-interceptions"
```

#### 1.3 Filter for Defensive Backs
```python
# Filter for player_position in ['CB', 'SS', 'FS', 'S']
# Ensure player_side == 'Defense'
# Group positions: safeties = ['SS', 'FS', 'S'], cornerbacks = ['CB']
```

---

### Phase 2: Feature Engineering

#### 2.1 Pre-Throw Features (from Input Data)

**Spatial Features:**
- Distance to ball landing location: `sqrt((x - ball_land_x)^2 + (y - ball_land_y)^2)`
- Initial distance from ball (frame 1)
- Minimum distance to ball across all pre-throw frames
- Average distance to ball
- Position relative to line of scrimmage (x vs absolute_yardline_number)
- Field position (hash mark proximity, sideline proximity)

**Kinematic Features:**
- Speed (s): mean, max, min, std across frames
- Acceleration (a): mean, max, change rate
- Speed at throw moment (last frame before throw)
- Acceleration at throw moment

**Directional Features:**
- Direction (dir): angle player is moving
- Orientation (o): angle player is facing
- Angular alignment: difference between dir and o (body control)
- Angle to ball: `atan2(ball_land_y - y, ball_land_x - x)`
- Direction alignment to ball: `abs(dir - angle_to_ball)`
- Orientation alignment to ball: `abs(o - angle_to_ball)`

**Temporal Features:**
- Rate of closing distance to ball landing spot
- Change in speed over time (derivative)
- Reaction timing (when player starts moving toward ball)

**Play Context Features (from Supplementary):**
- Coverage scheme (team_coverage_type)
- Man vs Zone (team_coverage_man_zone)
- Pass length (pass_length)
- Pass location (pass_location_type)
- Down and distance
- Defenders in box
- Score differential

#### 2.2 Post-Throw Features (from Output Data)

**Movement Metrics:**
- Total distance traveled post-throw: sum of frame-to-frame distances
- Average speed post-throw
- Final position (x, y at last frame)
- Distance to ball at catch point
- Convergence to ball: change in distance to ball over output frames

**Outcome Features:**
- Did player make interception (requires linking to play_description)
- Time to reach ball location (if applicable)
- Proximity ranking among all defenders on play

---

### Phase 3: Dataset Creation

#### 3.1 Primary Dataset: Interception Plays Only
```
Target: safeties_vs_cornerbacks_interceptions.csv

Rows: One row per defensive back per interception play
Columns:
- Identifiers: game_id, play_id, nfl_id, player_name, position_group
- Pre-throw spatial: initial_dist_to_ball, min_dist_to_ball, avg_dist_to_ball,
                     dist_from_los, field_position
- Pre-throw kinematic: avg_speed, max_speed, speed_at_throw, avg_accel, max_accel
- Pre-throw directional: avg_dir_alignment, avg_orient_alignment, body_control_score
- Pre-throw temporal: closing_rate, reaction_time_estimate
- Post-throw: total_dist_traveled, avg_speed_post, final_proximity_to_ball
- Play context: coverage_type, man_zone, pass_length, pass_location, down, distance
- Outcome: made_interception (binary), proximity_rank
```

#### 3.2 Comparison Dataset: Near-Miss Plays
```
Target: safeties_vs_cornerbacks_near_misses.csv

Same structure as above, but includes:
- Plays where pass_result == "IN" (incomplete)
- Filter for plays where a DB was within X yards of ball_land location
- Provides context for "almost interceptions"
```

#### 3.3 Aggregated Player Performance Dataset
```
Target: player_interception_profiles.csv

Rows: One row per player (aggregated across all their interception plays)
Columns:
- Player info: nfl_id, player_name, position, position_group
- Total plays involved in interception scenarios
- Mean/median of all pre-throw features
- Standard deviation of pre-throw features (consistency)
- Interception success rate
- Percentile rankings within position group
```

#### 3.4 Time-Series Dataset (Advanced)
```
Target: safeties_vs_cornerbacks_trajectories.csv

Rows: One row per player per frame per play
Columns:
- Identifiers: game_id, play_id, nfl_id, frame_id, position_group
- Frame data: x, y, s, a, dir, o
- Calculated: dist_to_ball, angle_to_ball, dir_alignment, orient_alignment
- Context: ball_land_x, ball_land_y, coverage_type, pass_result

Purpose: For trajectory analysis and time-series modeling
```

---

## Phase 4: Analysis Questions to Answer

### Primary Comparisons

1. **Positioning:**
   - Do safeties start farther from interception locations than CBs?
   - Do safeties cover more ground post-throw?

2. **Pre-Throw Awareness:**
   - Who has better directional alignment to ball landing spot?
   - Who shows earlier reaction (closing rate)?

3. **Speed vs Positioning Trade-off:**
   - Do CBs compensate for closer positioning with higher speed?
   - Do safeties rely more on anticipation (orientation) than speed?

4. **Context Effects:**
   - How does coverage scheme affect each position's effectiveness?
   - Zone vs Man coverage performance differences
   - Deep vs short pass scenarios

5. **Outcome Prediction:**
   - Which pre-throw features best predict interception success?
   - Do predictors differ between safeties and CBs?

---

## Phase 5: Statistical Approach

### Hypothesis Tests

**H1:** Safeties and CBs have significantly different average distances from ball at throw time
- Test: Independent t-test or Mann-Whitney U
- Effect size: Cohen's d

**H2:** Safeties and CBs differ in directional alignment to ball
- Test: Independent t-test
- Control for: coverage type, pass length

**H3:** Pre-throw speed predicts interception success differently for each position group
- Test: Logistic regression with interaction term
- Model: P(interception) ~ speed * position_group + controls

### Multivariate Analysis

**Cluster Analysis:**
- K-means clustering on pre-throw features
- Do safeties and CBs form distinct clusters?

**PCA/Dimensionality Reduction:**
- Identify principal components of DB performance
- Visualize position group separation

---

## Phase 6: Implementation Plan

### Step 1: Data Loading and Merging
```python
# Load all weeks of input/output data
# Merge with supplementary data
# Filter for interceptions
# Save to: data/interim/merged_tracking_data.csv
```

### Step 2: Feature Engineering
```python
# Calculate all pre-throw and post-throw features
# Create position_group column
# Save to: data/interim/engineered_features.csv
```

### Step 3: Dataset Creation
```python
# Create the 4 target datasets described above
# Save to: data/processed/
```

### Step 4: Exploratory Analysis
```python
# Notebook: notebooks/03_safeties_vs_cbs_exploration.ipynb
# Visualizations: distributions, correlations, position comparisons
```

### Step 5: Statistical Testing
```python
# Experiment: experiments/exp_002_position_comparison/
# Hypothesis testing, effect sizes, model fitting
```

### Step 6: Reporting
```python
# Generate visualizations comparing positions
# Create summary tables
# Compile findings into report
```

---

## Key Files to Create

```
data/interim/
├── merged_tracking_data.csv              # All weeks merged
├── engineered_features.csv               # All calculated features
└── interception_plays_only.csv           # Filtered interceptions

data/processed/
├── safeties_vs_cornerbacks_interceptions.csv
├── safeties_vs_cornerbacks_near_misses.csv
├── player_interception_profiles.csv
└── safeties_vs_cornerbacks_trajectories.csv

notebooks/
├── 03_safeties_vs_cbs_exploration.ipynb
├── 04_feature_engineering.ipynb
└── 05_trajectory_analysis.ipynb

experiments/
└── exp_002_safeties_vs_cbs/
    ├── README.md
    ├── hypothesis.md
    ├── config.yaml
    ├── analysis.py
    └── results/
```

---

## Expected Insights

1. **Positioning Hypothesis:** Safeties typically start 5-15 yards deeper than CBs on interception plays
2. **Speed Compensation:** CBs may have higher average speed but less optimal angles
3. **Coverage Context:** Zone coverage may favor safety interceptions, man coverage may favor CB
4. **Reaction Time:** Safeties may show better pre-throw orientation toward eventual ball location
5. **Success Factors:** Orientation alignment may be more predictive than raw speed for interceptions

---

## Tools and Libraries

- **Data Processing:** pandas, numpy
- **Feature Engineering:** scipy (for distance/angle calculations)
- **Statistical Analysis:** scipy.stats, statsmodels
- **Visualization:** matplotlib, seaborn, plotly (for trajectory animations)
- **Machine Learning:** scikit-learn (for clustering, PCA, classification)

---

## Next Steps

1. Create data loading pipeline script
2. Implement feature engineering functions in `src/data/transformers.py`
3. Create initial exploratory notebook
4. Design experiment structure for formal hypothesis testing
