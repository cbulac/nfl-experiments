# Quick Start Guide: Safeties vs Cornerbacks Experiment

## 🚀 Run the Complete Analysis

From the experiment directory:

```bash
cd experiments/exp_002_safeties_vs_cornerbacks

# Step 1: Load and merge data (5-10 minutes)
python scripts/load_and_merge_data.py

# Step 2: Engineer features (2-5 minutes)
python scripts/engineer_features.py

# Step 3: Run statistical analysis (< 1 minute)
python analysis.py
```

## 📊 View Results

After running the analysis, check:

```bash
# View statistical results
cat results/statistics.json

# View figures
ls -lh results/figures/
# - distance_comparison.png
# - speed_comparison.png
# - alignment_comparison.png

# View execution log
ls -lh logs/
```

## 🎯 What You'll Get

### Statistical Results
- H1: Are safeties positioned farther from the ball? (p-value, effect size)
- H2: Do safeties have better directional alignment? (p-value, effect size)
- H3: Are cornerbacks faster? (p-value, effect size)

### Visualizations
- Distribution comparisons for distance, speed, and alignment
- Box plots showing position group differences
- Summary statistics overlaid on plots

### Logs
- Detailed execution logs with timestamps
- Data loading progress
- Feature calculation summaries
- Test results and interpretations

## 🔧 Quick Customization

### Change Significance Level
Edit `config.yaml`:
```yaml
analysis:
  statistical_tests:
    alpha: 0.05  # Change from 0.01 to 0.05
```

### Analyze Specific Weeks
Edit `config.yaml`:
```yaml
data:
  weeks_to_process: [1, 2, 3]  # Only weeks 1-3
```

### Change Visualization Style
Edit `config.yaml`:
```yaml
visualization:
  style: "darkgrid"  # Or "whitegrid", "dark", "white", "ticks"
  dpi: 150  # Lower for faster generation
```

## 📈 Expected Runtime

- **Data Loading**: 5-10 minutes (depends on number of weeks)
- **Feature Engineering**: 2-5 minutes
- **Statistical Analysis**: < 1 minute
- **Total**: ~10-15 minutes

## 💾 Disk Space Requirements

- Input data: ~800 MB (all weeks)
- Merged data: ~200-300 MB
- Engineered features: ~50-100 MB
- Total: ~1.5 GB

## ❓ Troubleshooting

### "File not found" error
- Make sure you're in the correct directory
- Check that data files exist in `../../data/raw/`

### "No module named 'src'" error
```bash
# The scripts automatically add src to path, but if needed:
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../.."
```

### Memory issues
Reduce weeks processed in `config.yaml` or increase system RAM

### Matplotlib backend issues
Add to script if needed:
```python
import matplotlib
matplotlib.use('Agg')
```

## 🎓 Understanding the Output

### P-values
- **< 0.01**: Strong evidence against null hypothesis (with Bonferroni correction)
- **0.01-0.05**: Moderate evidence (not significant with correction)
- **> 0.05**: Weak evidence

### Effect Sizes (Cohen's d)
- **0.2**: Small practical difference
- **0.5**: Medium practical difference
- **0.8**: Large practical difference

### Confidence Intervals
- 95% CI not including 0 = statistically significant difference
- Width indicates precision of estimate

## 🔄 Rerunning Analysis

To rerun with different parameters:

1. Modify `config.yaml`
2. Rerun only the affected steps:
   - Changed data filters? → Rerun all 3 steps
   - Changed feature params? → Rerun steps 2 & 3
   - Changed statistical params? → Rerun step 3 only

## 📝 Next Steps After Analysis

1. **Review Results**: Check `results/statistics.json` for all test outcomes
2. **Examine Plots**: Visual inspection often reveals insights beyond statistics
3. **Read Logs**: Detailed information about sample sizes and data quality
4. **Interpret Findings**: See `hypothesis.md` for interpretation guidelines
5. **Extend Analysis**: Add new hypotheses or analyze subgroups

## 🆘 Need Help?

- Check `README.md` for detailed documentation
- Review `hypothesis.md` for statistical methodology
- Examine `config.yaml` for all configurable parameters
- Check logs in `logs/` directory for execution details
