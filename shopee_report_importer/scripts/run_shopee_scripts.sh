#!/bin/bash

# Shopee Report Download Wrapper Script
# Usage: ./run_shopee_scripts.sh <workspace_dir> [python_path]

WORKSPACE_DIR="$1"
PYTHON_PATH="$2"

if [ -z "$WORKSPACE_DIR" ]; then
    echo "Usage: $0 <workspace_dir> [python_path]"
    exit 1
fi

# Use provided Python path or auto-detect
if [ -n "$PYTHON_PATH" ] && [ -x "$PYTHON_PATH" ]; then
    PYTHON_CMD="$PYTHON_PATH"
    echo "Using provided Python: $PYTHON_CMD"
else
    # Auto-detect Python
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_CMD="python3"
    elif command -v python >/dev/null 2>&1; then
        PYTHON_CMD="python"
    else
        echo "Error: No Python interpreter found"
        exit 1
    fi
    echo "Using auto-detected Python: $PYTHON_CMD"
fi

if [ ! -d "$WORKSPACE_DIR" ]; then
    echo "Error: Workspace directory does not exist: $WORKSPACE_DIR"
    exit 1
fi

# Change to workspace directory
cd "$WORKSPACE_DIR"

# Set up logging
LOG_FILE="shopee_scripts.log"
echo "=== Shopee Scripts Execution Log ===" > "$LOG_FILE"
echo "Started at: $(date)" >> "$LOG_FILE"
echo "Python: $PYTHON_CMD" >> "$LOG_FILE"
echo "Workspace: $WORKSPACE_DIR" >> "$LOG_FILE"
echo "=================================" >> "$LOG_FILE"

# Set environment variables
export PYTHONPATH=""

# Log Python version and path info
echo "=== Python Info ===" >> "$LOG_FILE"
echo "Python command: $PYTHON_CMD" >> "$LOG_FILE"
"$PYTHON_CMD" --version >> "$LOG_FILE" 2>&1
"$PYTHON_CMD" -c "import sys; print('Python path:', sys.executable)" >> "$LOG_FILE" 2>&1
"$PYTHON_CMD" -c "import sys; print('Python paths:', sys.path)" >> "$LOG_FILE" 2>&1
echo "=== End Python Info ===" >> "$LOG_FILE"

# List of scripts to run
SCRIPTS=(
    "ads_cpc.py"
    "ads_live_local.py"
    "booking_local.py"
    "laban_local.py"
    "live_product.py"
    "order_local.py"
    "video_product.py"
)

# Function to run a script
run_script() {
    local script="$1"
    echo "Running $script with $PYTHON_CMD..."
    echo "Running $script with $PYTHON_CMD..." >> "$LOG_FILE"

    if [ ! -f "$script" ]; then
        echo "Warning: Script not found: $script"
        echo "ERROR: Script not found: $script" >> "$LOG_FILE"
        return 1
    fi

    # Run with the specified Python interpreter and capture output
    echo "--- Output for $script ---" >> "$LOG_FILE"
    "$PYTHON_CMD" "$script" >> "$LOG_FILE" 2>&1

    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        echo "✓ $script completed successfully"
        echo "SUCCESS: $script completed successfully" >> "$LOG_FILE"
    else
        echo "✗ $script failed with exit code $exit_code"
        echo "ERROR: $script failed with exit code $exit_code" >> "$LOG_FILE"
    fi
    echo "--- End output for $script ---" >> "$LOG_FILE"

    return $exit_code
}

# Run all scripts
echo "Starting Shopee report download..."
echo "Workspace: $WORKSPACE_DIR"
echo "Scripts to run: ${SCRIPTS[*]}"
echo "----------------------------------------"

echo "Starting Shopee report download..." >> "$LOG_FILE"
echo "Scripts to run: ${SCRIPTS[*]}" >> "$LOG_FILE"
echo "----------------------------------------" >> "$LOG_FILE"

SUCCESS_COUNT=0
TOTAL_COUNT=${#SCRIPTS[@]}

for script in "${SCRIPTS[@]}"; do
    if run_script "$script"; then
        ((SUCCESS_COUNT++))
    fi
    echo "----------------------------------------"
done

echo "Summary: $SUCCESS_COUNT/$TOTAL_COUNT scripts completed successfully"
echo "Summary: $SUCCESS_COUNT/$TOTAL_COUNT scripts completed successfully" >> "$LOG_FILE"
echo "Finished at: $(date)" >> "$LOG_FILE"

if [ $SUCCESS_COUNT -eq $TOTAL_COUNT ]; then
    echo "All scripts completed successfully" >> "$LOG_FILE"
    exit 0
else
    echo "Some scripts failed" >> "$LOG_FILE"
    exit 1
fi
