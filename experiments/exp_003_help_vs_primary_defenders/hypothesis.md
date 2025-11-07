# Hypothesis Statement: Help Defenders vs Primary Defenders in Interceptions

## Research Question
Are help defenders (secondary coverage providing assistance) more likely to successfully intercept passes compared to primary defenders (assigned to the targeted receiver)?

## Background & Rationale

In football defensive schemes, defenders are typically classified as:
- **Primary Defenders**: Assigned to cover the targeted receiver (man-to-man or zone responsibility)
- **Help Defenders**: Providing secondary support, reading the QB, positioned to help if beaten

**Theoretical Arguments:**

**For Help Defenders:**
- Better angles to the ball (not directly engaged)
- Can read QB eyes and ball trajectory
- Not physically engaged with receiver
- Element of surprise for QB
- Can time their break on the ball

**Against Help Defenders (For Primary):**
- Closer proximity to target receiver
- Already in the play's immediate area
- First opportunity to contest the catch
- Better positioning on underthrown balls

## Primary Hypothesis

### H1: Interception Rate by Defender Type
**Null Hypothesis (H₀):** There is no difference in interception success rate between help defenders and primary defenders.

**Alternative Hypothesis (H₁):** Help defenders have a significantly higher interception success rate than primary defenders (one-tailed test).

**Expected Direction:** Help Defenders > Primary Defenders

**Statistical Test:**
- Test Type: Chi-square test of independence or Two-proportion z-test
- Contingency table: [Defender Type × Made Interception]
- Significance Level (α): 0.05
- Expected Effect Size: OR ≈ 1.5-2.0 (moderate odds ratio)

**Success Criteria:**
- p-value < 0.05
- Odds ratio > 1.3 with 95% CI not including 1.0

---

## Secondary Hypotheses

### H2: Proximity Differences
**Null Hypothesis (H₀):** There is no difference in average distance to ball landing location between help defenders and primary defenders.

**Alternative Hypothesis (H₁):** Primary defenders are positioned closer to the ball landing location than help defenders (one-tailed test).

**Rationale:** Primary defenders should be closer by definition (covering the target).

**Statistical Test:**
- Test Type: Independent t-test (or Mann-Whitney U)
- Metric: `initial_dist_to_ball`
- Significance Level (α): 0.05
- Expected Effect Size: Cohen's d ≈ 0.5-0.8 (medium to large)

---

### H3: Speed Compensation
**Null Hypothesis (H₀):** There is no difference in average speed between help defenders who intercept and primary defenders who intercept.

**Alternative Hypothesis (H₁):** Help defenders who successfully intercept show higher speed than primary defenders who intercept (two-tailed test).

**Rationale:** Help defenders may need to close distance faster to reach the ball.

**Statistical Test:**
- Test Type: Independent t-test
- Metric: `avg_speed` (for intercepting players only)
- Significance Level (α): 0.05
- Expected Effect Size: Cohen's d ≈ 0.3-0.5

---

### H4: Angle Advantage
**Null Hypothesis (H₀):** There is no difference in directional alignment between help defenders who intercept and primary defenders who intercept.

**Alternative Hypothesis (H₁):** Help defenders who successfully intercept demonstrate better directional alignment to the ball than primary defenders who intercept (one-tailed test).

**Rationale:** Help defenders can break on the ball with better angles.

**Statistical Test:**
- Test Type: Independent t-test
- Metric: `avg_dir_alignment` (lower = better)
- Significance Level (α): 0.05
- Expected Effect Size: Cohen's d ≈ 0.3-0.5

---

### H5: Position Group Interaction
**Null Hypothesis (H₀):** The effect of defender type (help vs. primary) on interception rate does not differ between cornerbacks and safeties.

**Alternative Hypothesis (H₁):** The help defender advantage differs significantly between cornerbacks and safeties.

**Statistical Test:**
- Test Type: Logistic regression with interaction term
- Model: P(INT) ~ defender_type × position_group + controls
- Significance Level (α): 0.05

---

## Operational Definitions

### Defining Defender Types

Since the dataset doesn't explicitly label "primary" vs "help" defenders, we'll use the following proxy methods:

#### **Method 1: Proximity-Based (Primary Method)**
- **Primary Defender**: Closest defensive back to the ball landing location at throw moment
  - `rank(initial_dist_to_ball) == 1` per play
- **Help Defender**: Any other defensive back on the play
  - `rank(initial_dist_to_ball) > 1` per play

**Advantages:**
- Objective and data-driven
- Closest defender is most likely the assigned coverage
- Clear operational definition

**Limitations:**
- May misclassify some zone defenders
- Doesn't account for route depth

---

#### **Method 2: Distance Threshold (Secondary Validation)**
- **Primary Defender**: Within 5 yards of ball landing location
- **Help Defender**: >5 yards from ball landing location

**Advantages:**
- Captures "in the vicinity" concept
- Allows multiple primary defenders (bracket coverage)

---

#### **Method 3: Player Role (If Available)**
If `player_role` field indicates targeted receiver coverage:
- Use explicit role assignments from data

---

### Defining Interception Success

**Made Interception:**
- Player is marked as `player_to_predict == True` in the data
- OR: Player has smallest `final_proximity_to_ball` AND `pass_result == 'I'`
- OR: Identified through play description parsing

**Did Not Intercept:**
- All other defensive backs on interception plays

---

## Sample Size & Power Analysis

### Expected Sample Breakdown

Based on previous analysis:
- Total interception plays: 4,032
- Average DBs per play: ~5
- Total DB observations: 19,813

**Expected Distribution:**
- Primary defenders per play: ~1-2 players (20-40%)
- Help defenders per play: ~3-4 players (60-80%)

**Expected Interception Rates:**
- Primary defenders: ~15-25% (1 in 4-7 primary defenders makes INT)
- Help defenders: ~10-15% (if hypothesis false) or ~20-30% (if hypothesis true)

### Power Calculation

For two-proportion test:
- Desired Power: 0.80
- Significance Level: 0.05
- Expected proportions: p₁ = 0.20, p₂ = 0.30
- **Minimum Sample Size:** ~200 per group

**Expected Sample Size:** 4,000-8,000 primary, 12,000-15,000 help
- **Conclusion:** Extremely well-powered for detection

---

## Control Variables

To isolate the effect of defender type, control for:

1. **Position Group:** Cornerback vs. Safety
2. **Coverage Type:** Man vs. Zone
3. **Pass Characteristics:**
   - Pass length (short, medium, deep)
   - Pass location (inside, outside)
4. **Game Situation:**
   - Down and distance
   - Quarter
5. **Player Characteristics:**
   - Speed
   - Acceleration

---

## Analysis Plan

### Phase 1: Data Preparation
1. Load engineered features from exp_002
2. Define defender types using proximity ranking
3. Identify which player made the interception (from `player_to_predict` or proximity)
4. Create binary outcome: `made_interception`
5. Label each observation as `primary` or `help`

### Phase 2: Descriptive Analysis
1. Interception rate by defender type
2. Sample sizes and distributions
3. Baseline characteristics comparison

### Phase 3: Primary Hypothesis Test (H1)
1. 2×2 contingency table: [Defender Type × Made INT]
2. Chi-square test
3. Calculate odds ratio and relative risk
4. Proportion test with confidence intervals

### Phase 4: Secondary Analyses (H2-H5)
1. Compare positioning metrics
2. Compare speed metrics (for successful interceptors)
3. Compare alignment metrics
4. Test position group interactions

### Phase 5: Multivariate Analysis
1. Logistic regression controlling for confounders
2. Model: `P(INT) ~ defender_type + position_group + coverage_type + pass_length + speed`
3. Report adjusted odds ratios

### Phase 6: Sensitivity Analysis
1. Vary proximity threshold (rank 1 vs. rank 2)
2. Vary distance threshold (3, 5, 7 yards)
3. Separate analysis by coverage type
4. Separate analysis by position group

---

## Expected Results

### Scenario A: Help Defenders Have Advantage (Hypothesis Supported)
- Help defender interception rate: 25-30%
- Primary defender interception rate: 15-20%
- Odds Ratio: 1.5-2.0
- Interpretation: Help defenders benefit from better angles and QB reads

### Scenario B: Primary Defenders Have Advantage (Hypothesis Contradicted)
- Primary defender interception rate: 30-40%
- Help defender interception rate: 10-15%
- Odds Ratio: 0.3-0.5
- Interpretation: Proximity dominates; closest player has best chance

### Scenario C: No Difference (Null Hypothesis)
- Both ~20% interception rate
- Odds Ratio: 0.9-1.1
- Interpretation: Role doesn't matter; situation and skill dominate

---

## Potential Confounders

1. **Position Bias:** Safeties more often play help, CBs more often primary
2. **Coverage Scheme:** Zone coverage may blur primary/help distinction
3. **Pass Quality:** Poorly thrown passes benefit whoever is near
4. **Player Skill:** Elite players succeed regardless of role
5. **Sample Selection:** Only interception plays included (selection bias)

**Mitigation:**
- Use multivariate models with controls
- Stratified analysis by position and coverage
- Sensitivity analyses

---

## Interpretation Guidelines

### Statistical Significance
- p < 0.05: Reject null hypothesis
- Report exact p-values
- Multiple comparison correction if testing many subgroups

### Effect Size (Odds Ratio)
- OR = 1.0: No effect
- OR = 1.5: 50% higher odds for help defenders
- OR = 2.0: Double the odds for help defenders
- OR < 1.0: Primary defenders have advantage

### Practical Significance
Even if statistically significant, consider:
- Is the effect size large enough to matter?
- Does it apply across all situations?
- What are the coaching implications?

---

## Success Criteria Summary

| Hypothesis | Metric | Success Threshold |
|------------|--------|-------------------|
| H1: INT Rate | Odds Ratio | OR > 1.3, p < 0.05 |
| H2: Proximity | Cohen's d | d > 0.5, p < 0.05 |
| H3: Speed | Cohen's d | \|d\| > 0.3, p < 0.05 |
| H4: Angle | Cohen's d | d > 0.3, p < 0.05 |
| H5: Interaction | p-value | p < 0.05 for interaction term |

---

## Limitations & Caveats

1. **Role Inference:** We infer roles from proximity, not true assignments
2. **Selection Bias:** Only interception plays analyzed (not all passes)
3. **Causality:** Correlation doesn't prove role causes INT success
4. **Scheme Variation:** Different teams employ different philosophies
5. **Player Quality:** Not controlling for individual player skill levels

---

## Alternative Hypotheses to Explore

If primary hypothesis fails, investigate:
1. **Distance Bins:** Does effect vary by initial distance (0-5y, 5-10y, >10y)?
2. **Coverage Type Specific:** Help advantage in zone but not man?
3. **Pass Length Specific:** Help advantage on deep balls only?
4. **Position Specific:** Help advantage for safeties but not CBs?
5. **Bracket Coverage:** When 2 primary defenders, does help still matter?

---

## Validation Strategy

To ensure robustness:
1. **Train/Test Split:** Validate on held-out data (weeks 1-12 vs. 13-18)
2. **Cross-Validation:** 5-fold CV for models
3. **Bootstrap CIs:** 1000 bootstrap samples for odds ratios
4. **Sensitivity Analysis:** Vary key thresholds and definitions

---

## Expected Insights

This experiment will reveal:
1. Whether defensive back roles predict interception success
2. The optimal positioning strategy for interceptions
3. Whether help defense concepts apply to actual outcomes
4. How position groups differ in primary vs. help effectiveness
5. Actionable insights for defensive coaching and strategy

---

## Timeline & Deliverables

**Data Preparation:** 30 minutes
**Analysis Execution:** 10 minutes
**Visualization Generation:** 5 minutes
**Report Writing:** Automatic

**Deliverables:**
1. Contingency tables and interception rates
2. Odds ratios with confidence intervals
3. Comparison visualizations (rates, positions, angles)
4. Multivariate model results
5. Sensitivity analysis results
6. Executive summary with coaching implications

---

*This hypothesis tests a fundamental defensive football concept using objective tracking data, potentially validating or challenging conventional wisdom about help defense effectiveness.*
