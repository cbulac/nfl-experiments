# Hypothesis Statement: Safeties vs Cornerbacks in Interception Scenarios

## Research Question
How do safeties and cornerbacks differ in their pre-throw positioning, movement, and orientation characteristics during plays that result in interceptions, and which factors most strongly predict interception success for each position group?

## Primary Hypotheses

### H1: Initial Positioning Differences
**Null Hypothesis (H₀):** There is no significant difference in average distance from ball landing location between safeties and cornerbacks at the moment of QB throw.

**Alternative Hypothesis (H₁):** Safeties are positioned significantly farther from the ball landing location than cornerbacks at the moment of QB throw (one-tailed test).

**Expected Direction:** Safeties > Cornerbacks (safeties play deeper)

**Statistical Test:**
- Test Type: Independent samples t-test (or Welch's t-test if variances unequal)
- Significance Level (α): 0.05
- Expected Effect Size: Cohen's d ≈ 0.6 - 0.8 (medium to large effect)
- Sample: All defensive backs on interception plays

**Success Criteria:**
- p-value < 0.05 with mean_distance(safeties) > mean_distance(cornerbacks)
- Effect size d > 0.5

---

### H2: Directional Alignment and Anticipation
**Null Hypothesis (H₀):** There is no significant difference in average directional alignment to ball landing location between safeties and cornerbacks prior to QB throw.

**Alternative Hypothesis (H₁):** Safeties demonstrate better directional alignment (smaller angle difference) to the ball landing location than cornerbacks during pre-throw frames (two-tailed test).

**Rationale:** Safeties may have better field vision and anticipation due to their deeper positioning.

**Statistical Test:**
- Test Type: Independent samples t-test
- Significance Level (α): 0.05
- Expected Effect Size: Cohen's d ≈ 0.3 - 0.5 (small to medium effect)
- Control Variables: Coverage type, pass length

**Success Criteria:**
- p-value < 0.05
- |d| > 0.3

---

### H3: Speed Compensation Hypothesis
**Null Hypothesis (H₀):** There is no relationship between initial distance from ball and average speed for either position group.

**Alternative Hypothesis (H₁):** Cornerbacks demonstrate higher average speed than safeties, compensating for their closer initial positioning (two-tailed test).

**Statistical Test:**
- Test Type: Independent samples t-test for speed comparison
- Additional: Correlation analysis between distance and speed within each group
- Significance Level (α): 0.05
- Expected Effect Size: Cohen's d ≈ 0.4 (medium effect)

**Success Criteria:**
- p-value < 0.05 with mean_speed(cornerbacks) > mean_speed(safeties)

---

### H4: Coverage Scheme Interaction Effect
**Null Hypothesis (H₀):** Coverage scheme (zone vs man) does not differentially affect interception involvement rates between safeties and cornerbacks.

**Alternative Hypothesis (H₁):** The ratio of safeties to cornerbacks involved in interceptions differs significantly between zone and man coverage schemes.

**Statistical Test:**
- Test Type: Chi-square test of independence or logistic regression with interaction term
- Significance Level (α): 0.05
- Model: position_group ~ coverage_type

**Success Criteria:**
- Chi-square p-value < 0.05 or
- Significant interaction term in logistic regression (p < 0.05)

---

### H5: Predictive Features Differ by Position
**Null Hypothesis (H₀):** The same set of features predicts interception success equally well for both safeties and cornerbacks.

**Alternative Hypothesis (H₁):** Different features (speed, alignment, positioning) have significantly different predictive power for interception success between safeties and cornerbacks.

**Statistical Test:**
- Test Type: Logistic regression with interaction terms
- Model: P(made_interception) ~ speed × position_group + alignment × position_group + distance × position_group + controls
- Significance Level (α): 0.05

**Success Criteria:**
- At least one interaction term significant at p < 0.05
- Different AUC/accuracy when predicting separately for each position group

---

## Secondary Research Questions

### Q1: Post-Throw Movement Patterns
Do safeties cover more total distance after the throw compared to cornerbacks?
- **Test:** Independent samples t-test on total_distance_traveled
- **Hypothesis:** Safeties travel farther (due to initial distance)

### Q2: Reaction Time Differences
Do safeties show earlier directional changes toward the ball landing location?
- **Test:** Time-series analysis of direction changes
- **Metric:** Frame number where player begins closing on ball location

### Q3: Consistency Analysis
Which position group shows more consistent performance across plays?
- **Test:** Levene's test for equality of variances
- **Metric:** Standard deviation of key features within position group

---

## Assumptions

### Statistical Assumptions
1. **Independence:** Each play represents an independent observation
   - Check: Verify no repeated measures issues
2. **Normality:** Key continuous variables are approximately normally distributed
   - Check: Shapiro-Wilk test, Q-Q plots
   - Backup: Use Mann-Whitney U if normality violated
3. **Homogeneity of Variance:** Equal variances between groups (for standard t-test)
   - Check: Levene's test
   - Backup: Use Welch's t-test if violated

### Domain Assumptions
1. Player positions are accurately recorded in the data
2. Ball landing coordinates represent actual catch/interception location
3. Interception plays represent scenarios where DBs had legitimate opportunity
4. Coverage assignments are correctly coded in supplementary data

---

## Sample Size Considerations

### Power Analysis
- Desired Power (1-β): 0.80
- Significance Level (α): 0.05
- Expected Effect Size: d = 0.5 (medium)
- **Minimum Sample Size:** ~64 per group (128 total)

### Expected Sample Sizes
Based on preliminary data exploration:
- Estimated interceptions per week: ~15-25 plays
- Estimated DBs per interception play: ~4-6 players
- Total weeks available: 15-18
- **Expected Total Sample:** ~900-2700 DB-play observations

**Breakdown Estimate:**
- Cornerbacks: ~60% of sample (~540-1620 observations)
- Safeties: ~40% of sample (~360-1080 observations)

This should provide adequate power for all planned analyses.

---

## Multiple Comparison Correction

Given multiple hypothesis tests, we will apply corrections:
- **Method:** Bonferroni correction for 5 primary hypotheses
- **Adjusted α:** 0.05 / 5 = 0.01 per test
- **Alternative:** False Discovery Rate (FDR) control if assumptions violated

---

## Success Metrics Summary

| Hypothesis | Metric | Success Threshold |
|------------|--------|-------------------|
| H1: Positioning | Cohen's d | > 0.5, p < 0.01 |
| H2: Alignment | Cohen's d | > 0.3, p < 0.01 |
| H3: Speed | Cohen's d | > 0.4, p < 0.01 |
| H4: Coverage | χ² or interaction p | < 0.01 |
| H5: Predictors | Interaction term p | < 0.01 |

---

## Validation Strategy

1. **Train/Test Split:** 80/20 split for predictive models
2. **Cross-Validation:** 5-fold CV for model validation
3. **Robustness Checks:**
   - Analyze by coverage type separately
   - Analyze by pass length categories
   - Check for week-to-week consistency

---

## Expected Outcomes

Based on football domain knowledge:

1. ✓ H1 will likely be supported (safeties play deeper)
2. ? H2 uncertain (could go either way)
3. ✓ H3 likely supported (CBs are typically faster)
4. ✓ H4 likely supported (zone favors safeties)
5. ✓ H5 likely supported (positions have different roles)

The analysis will provide quantitative evidence for these expectations and may reveal surprising insights about defensive back play in interception scenarios.
