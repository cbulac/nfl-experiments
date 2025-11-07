# Strategy: Adding Defender Tracking for True Separation Metrics

**Date:** 2025-11-06
**Purpose:** Calculate accurate separation from nearest defender at throw moment

---

## Available Data

### Tracking Data Fields (input_2023_wXX.csv)
- `game_id`, `play_id`, `frame_id` - Play identifiers
- `nfl_id`, `player_name`, `player_position` - Player identification
- `player_side` - "Offense" or "Defense"
- `player_role` - "Defensive Coverage", "Passer", "Other Route Runner", etc.
- `x`, `y` - Player coordinates on field
- `s`, `a`, `dir`, `o` - Speed, acceleration, direction, orientation
- `ball_land_x`, `ball_land_y` - Ball landing location (constant per play)

### Defensive Positions Available
**Coverage positions:**
- CB (Cornerback)
- FS (Free Safety)
- SS (Strong Safety)
- S (Safety - unspecified)
- ILB, MLB, OLB (Linebackers in coverage)
- DE, DT, NT (Defensive line - rarely in coverage)

---

## Strategy

### 1. Identify Target Receiver for Each Play
**Current approach (from previous analyses):**
- Use `player_to_predict=True` to identify target receiver
- Alternative: Use supplementary data `targetNflId` field

### 2. Identify "Throw Moment" Frame
**Options:**
a) **Last frame** (max_frame_id) - Current approach
   - Pros: Simple, consistent
   - Cons: May include post-throw movement

b) **Frame where ball leaves QB hand** (need to detect)
   - Pros: Most accurate "throw moment"
   - Cons: Requires detecting ball release (complex)

c) **Frame N frames before last** (e.g., last - 2 frames)
   - Pros: Accounts for ball flight time
   - Cons: Arbitrary offset

**Recommendation:** Start with last frame (max_frame_id), validate results

### 3. Find Nearest Defender at Throw Frame
**Algorithm:**
```python
For each play:
  1. Get throw_frame_id = max(frame_id)
  2. Filter to throw_frame_id only
  3. Get target receiver position (x_receiver, y_receiver)
  4. Get all defensive players on same frame
  5. Calculate distance from receiver to each defender:
     distance = sqrt((x_def - x_rec)^2 + (y_def - y_rec)^2)
  6. Find minimum distance
  7. Store: nearest_defender_id, nearest_defender_position, separation_distance
```

**Filtering defensive players:**
- Include: `player_side == "Defense"`
- Include: `player_role == "Defensive Coverage"` (optional - may exclude DL)
- OR filter by position: CB, FS, SS, S, ILB, MLB, OLB

### 4. Calculate Separation Metrics

**Primary Metric:**
- **Separation at Throw** = Euclidean distance to nearest defender (yards)

**Secondary Metrics:**
- **Nearest Defender Position** (CB, S, LB) - coverage type indicator
- **Coverage Cushion** = Separation at snap (frame_id = 1)
- **Separation Change** = (separation at throw) - (separation at snap)
- **Defender Closing Speed** = separation_change / time_to_throw

**Coverage Context:**
- Count defenders within 3 yards (bracket coverage)
- Count defenders within 5 yards (zone help)
- Nearest defender speed at throw (converging or trailing)

### 5. Validation Strategy

**Expected Values for HITCH Routes:**
- HITCH route depth: ~3 yards
- Expected separation: 2-5 yards (reasonable range)
- Completion % should correlate with separation (r > 0.3)

**Sanity Checks:**
- Separation should be < route distance traveled (can't be 15 yards on 3-yard route)
- Average separation on completions > average on incompletions
- Faster receivers should create more separation (positive correlation)

**Test Cases:**
1. Sample 10 random HITCH routes, manually verify separation looks reasonable
2. Compare to previous (incorrect) metric - should be ~3-5x smaller
3. Check separation by route type (HITCH < OUT < GO)

---

## Implementation Plan

### Step 1: Create `add_defender_tracking.py` Script
**Inputs:**
- All tracking files: `data/raw/train/input_2023_wXX.csv`
- Supplementary data: `data/raw/supplementary_data.csv` (enhanced with time_to_throw)

**Outputs:**
- `data/processed/defender_separation.csv` - One row per targeted play
  - Columns: game_id, play_id, nfl_id (receiver), separation_at_throw, nearest_defender_id, nearest_defender_position, coverage_cushion, separation_change, defenders_within_3yd, defenders_within_5yd

**Processing:**
```python
1. Load all tracking files, concatenate
2. Join with supplementary data to get targeted plays
3. For each targeted play:
   - Filter to throw frame (max_frame_id)
   - Get target receiver position
   - Get all defensive players
   - Calculate distances, find minimum
   - Calculate secondary metrics
4. Save results
```

### Step 2: Merge into Supplementary Data
**Enhanced supplementary data:**
- Add separation columns to existing enhanced_supplemental_data.csv
- Keep original columns, append new separation metrics

### Step 3: Re-run HITCH Route Analysis
**Updated `hitch_route_analysis.py`:**
- Replace `final_dist_to_ball` with `separation_at_throw`
- Add new metrics: coverage_cushion, separation_change, nearest_defender_position
- Compare by archetype

**Expected Results:**
- Precision Technicians: 3-4 yard separation (lower than Masters)
- HITCH Masters: 4-5 yard separation (higher, faster route break)
- Completion % should correlate with separation (r > 0.3)

### Step 4: Validate Results
**Validation checks:**
1. Mean separation by route type (HITCH < OUT < CORNER < GO)
2. Correlation: separation vs completion % (expect r > 0.3)
3. Correlation: speed vs separation (expect r > 0.2)
4. Sample 10 random plays, manually verify

---

## Alternative Approaches (Future Enhancements)

### 1. Multiple Defender Tracking
Instead of just nearest defender, track:
- Primary defender (man coverage - nearest at snap, stays nearest)
- Help defender (zone - arrives after route break)
- Bracket coverage detection (2+ defenders within 3 yards)

### 2. Dynamic Throw Moment Detection
Detect actual QB release frame:
- Look for sudden deceleration of QB
- Look for ball starting to move away from QB
- Use frame where `ball_land_x/y` first appears (if available)

### 3. Separation Timeline
Calculate separation at multiple moments:
- At snap (frame_id=1)
- At route break point (80% of route)
- At throw (max_frame_id)
- Separation velocity (rate of change)

### 4. Coverage Type Classification
Use defender positions and spacing to classify:
- Man coverage (1 defender shadowing receiver)
- Zone coverage (defenders stationary, receiver runs into space)
- Bracket coverage (2+ defenders within 3 yards)
- Press coverage (defender within 1 yard at snap)

---

## Expected Impact on HITCH Analysis

### Current (Incorrect) Metric:
- "Separation at Throw": 13-15 yards
- Actually: Distance from receiver to ball landing spot
- Includes YAC, incomplete trajectory

### New (Correct) Metric:
- **Expected separation at throw: 3-5 yards**
- HITCH route depth ~3 yards, separation should be similar magnitude
- Faster receivers (HITCH Masters) should create more separation

### Hypothesis Re-Test:
**Question:** Do Precision Technicians execute HITCHes better, or is it necessity?

**Expected Results with TRUE separation:**
- HITCH Masters: Higher separation (4-5 yards) - faster route break
- Precision Technicians: Lower separation (3-4 yards) - slower
- Correlation: Speed → Separation should strengthen (r > 0.3)
- Conclusion: **Still NECESSITY** - slower receivers create less separation

---

## Bottom Line

This strategy will:
1. ✅ Use existing tracking data (no new data needed)
2. ✅ Calculate true separation from nearest defender
3. ✅ Validate against expected values (2-5 yards for HITCH)
4. ✅ Re-test HITCH analysis with correct metric
5. ✅ Strengthen "necessity" conclusion with accurate separation data

**Implementation Estimate:** ~2-3 hours
- 1 hour: Write `add_defender_tracking.py` script
- 30 min: Process all 18 weeks of tracking data
- 30 min: Merge into supplementary data
- 30 min: Re-run HITCH analysis with new metric
- 30 min: Validation and comparison
