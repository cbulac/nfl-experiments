#!/bin/bash
# Script to run all experiments in the experiments directory

set -e

EXPERIMENTS_DIR="experiments"
LOG_FILE="experiments_batch_run.log"

echo "Starting batch experiment execution..."
echo "Log file: $LOG_FILE"
echo ""

# Initialize log file
echo "Batch Experiment Run - $(date)" > "$LOG_FILE"
echo "================================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Counter for tracking
TOTAL=0
SUCCESS=0
FAILED=0

# Find all experiment directories (exclude template)
for exp_dir in "$EXPERIMENTS_DIR"/*/; do
    # Skip template directory
    if [[ "$exp_dir" == *"template"* ]]; then
        continue
    fi

    # Check if analysis.py exists
    if [ -f "$exp_dir/analysis.py" ]; then
        TOTAL=$((TOTAL + 1))
        exp_name=$(basename "$exp_dir")

        echo "Running experiment: $exp_name"
        echo "Running experiment: $exp_name" >> "$LOG_FILE"
        echo "-----------------------------------" >> "$LOG_FILE"

        # Run the experiment
        if (cd "$exp_dir" && python analysis.py >> "../../$LOG_FILE" 2>&1); then
            echo "  ✓ Success"
            echo "  Status: SUCCESS" >> "$LOG_FILE"
            SUCCESS=$((SUCCESS + 1))
        else
            echo "  ✗ Failed (see log for details)"
            echo "  Status: FAILED" >> "$LOG_FILE"
            FAILED=$((FAILED + 1))
        fi

        echo "" >> "$LOG_FILE"
    fi
done

# Summary
echo ""
echo "================================================"
echo "Batch Execution Summary"
echo "================================================"
echo "Total experiments: $TOTAL"
echo "Successful: $SUCCESS"
echo "Failed: $FAILED"
echo ""
echo "Detailed log available at: $LOG_FILE"

# Add summary to log
echo "================================================" >> "$LOG_FILE"
echo "Summary" >> "$LOG_FILE"
echo "================================================" >> "$LOG_FILE"
echo "Total: $TOTAL | Success: $SUCCESS | Failed: $FAILED" >> "$LOG_FILE"
echo "Completed: $(date)" >> "$LOG_FILE"
