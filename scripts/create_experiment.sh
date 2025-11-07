#!/bin/bash
# Script to create a new experiment from template

set -e

# Check if experiment name is provided
if [ -z "$1" ]; then
    echo "Usage: ./create_experiment.sh <experiment_name>"
    echo "Example: ./create_experiment.sh exp_002_feature_analysis"
    exit 1
fi

EXPERIMENT_NAME=$1
EXPERIMENTS_DIR="experiments"
TEMPLATE_DIR="$EXPERIMENTS_DIR/template"
NEW_EXPERIMENT_DIR="$EXPERIMENTS_DIR/$EXPERIMENT_NAME"

# Check if template exists
if [ ! -d "$TEMPLATE_DIR" ]; then
    echo "Error: Template directory not found at $TEMPLATE_DIR"
    exit 1
fi

# Check if experiment already exists
if [ -d "$NEW_EXPERIMENT_DIR" ]; then
    echo "Error: Experiment $EXPERIMENT_NAME already exists!"
    exit 1
fi

# Create new experiment from template
echo "Creating new experiment: $EXPERIMENT_NAME"
cp -r "$TEMPLATE_DIR" "$NEW_EXPERIMENT_DIR"

# Create results and logs directories
mkdir -p "$NEW_EXPERIMENT_DIR/results/figures"
mkdir -p "$NEW_EXPERIMENT_DIR/logs"

# Add .gitkeep files
touch "$NEW_EXPERIMENT_DIR/results/.gitkeep"
touch "$NEW_EXPERIMENT_DIR/results/figures/.gitkeep"
touch "$NEW_EXPERIMENT_DIR/logs/.gitkeep"

# Update experiment name in config file
if [ -f "$NEW_EXPERIMENT_DIR/config.yaml" ]; then
    sed -i "s/exp_XXX_name/$EXPERIMENT_NAME/g" "$NEW_EXPERIMENT_DIR/config.yaml"
    # Update date
    TODAY=$(date +%Y-%m-%d)
    sed -i "s/YYYY-MM-DD/$TODAY/g" "$NEW_EXPERIMENT_DIR/config.yaml"
fi

# Update experiment name in README
if [ -f "$NEW_EXPERIMENT_DIR/README.md" ]; then
    sed -i "s/\[NUMBER\]/$(echo $EXPERIMENT_NAME | grep -oP '\d+')/g" "$NEW_EXPERIMENT_DIR/README.md"
    sed -i "s/\[TITLE\]/$EXPERIMENT_NAME/g" "$NEW_EXPERIMENT_DIR/README.md"
    TODAY=$(date +%Y-%m-%d)
    sed -i "s/YYYY-MM-DD/$TODAY/g" "$NEW_EXPERIMENT_DIR/README.md"
fi

echo "✓ Experiment created successfully at: $NEW_EXPERIMENT_DIR"
echo ""
echo "Next steps:"
echo "1. Edit $NEW_EXPERIMENT_DIR/hypothesis.md to define your hypothesis"
echo "2. Update $NEW_EXPERIMENT_DIR/config.yaml with experiment parameters"
echo "3. Implement your analysis in $NEW_EXPERIMENT_DIR/analysis.py"
echo "4. Run the experiment: cd $NEW_EXPERIMENT_DIR && python analysis.py"
