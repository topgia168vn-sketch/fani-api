#!/bin/bash

# Master Shopee Script Runner
# Quét tất cả workspace và chạy parallel run_shopee_scripts.sh
# Usage: ./master_shopee_runner.sh [filestore_path] [python_path]

# Get filestore path from argument or auto-detect
if [ -n "$1" ]; then
    FILESTORE_PATH="$1"
else
    # Auto-detect filestore path (common locations)
    if [ -d "/var/lib/odoo/filestore" ]; then
        FILESTORE_PATH="/var/lib/odoo/filestore"
    elif [ -d "/opt/odoo/filestore" ]; then
        FILESTORE_PATH="/opt/odoo/filestore"
    elif [ -d "./filestore" ]; then
        FILESTORE_PATH="./filestore"
    else
        echo "Error: Cannot auto-detect filestore path. Please provide it as argument."
        echo "Usage: $0 <filestore_path> [python_path]"
        exit 1
    fi
fi

# Get Python path from argument or auto-detect
if [ -n "$2" ] && [ -x "$2" ]; then
    PYTHON_PATH="$2"
    echo "Using provided Python: $PYTHON_PATH"
else
    # Auto-detect Python
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_PATH="python3"
    elif command -v python >/dev/null 2>&1; then
        PYTHON_PATH="python"
    else
        echo "Error: No Python interpreter found"
        exit 1
    fi
    echo "Using auto-detected Python: $PYTHON_PATH"
fi

# Set up paths
SHOPEE_SCRIPTS_DIR="$FILESTORE_PATH/shopee_scripts"
LOG_FILE="$SHOPEE_SCRIPTS_DIR/master_runner.log"
PID_FILE="$SHOPEE_SCRIPTS_DIR/master_runner.pid"

# Create shopee_scripts directory if not exists
mkdir -p "$SHOPEE_SCRIPTS_DIR"

# Check if already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "Master runner already running with PID $OLD_PID"
        exit 1
    else
        # Remove stale PID file
        rm -f "$PID_FILE"
    fi
fi

# Write current PID
echo $$ > "$PID_FILE"

# Set up logging
echo "=== Master Shopee Runner ===" > "$LOG_FILE"
echo "Started at: $(date)" >> "$LOG_FILE"
echo "Filestore: $FILESTORE_PATH" >> "$LOG_FILE"
echo "Python: $PYTHON_PATH" >> "$LOG_FILE"
echo "Scripts dir: $SHOPEE_SCRIPTS_DIR" >> "$LOG_FILE"
echo "=========================" >> "$LOG_FILE"

# Function to run workspace
run_workspace() {
    local workspace_dir="$1"
    local shop_id=$(basename "$workspace_dir" | sed 's/shop_//')

    echo "Processing shop $shop_id: $workspace_dir"
    echo "Processing shop $shop_id: $workspace_dir" >> "$LOG_FILE"

    # Check if workspace has required files
    if [ ! -f "$workspace_dir/cookies_shopee.json" ]; then
        echo "Warning: No cookies file in $workspace_dir"
        echo "Warning: No cookies file in $workspace_dir" >> "$LOG_FILE"
        return 1
    fi

    if [ ! -f "$workspace_dir/run_shopee_scripts.sh" ]; then
        echo "Warning: No run_shopee_scripts.sh in $workspace_dir"
        echo "Warning: No run_shopee_scripts.sh in $workspace_dir" >> "$LOG_FILE"
        return 1
    fi

    # Create downloads directory
    mkdir -p "$workspace_dir/downloads"

    # Run the workspace script
    cd "$workspace_dir"
    echo "Running scripts for shop $shop_id..."
    echo "Running scripts for shop $shop_id..." >> "$LOG_FILE"

    # Run with timeout (30 minutes)
    timeout 1800 ./run_shopee_scripts.sh . "$PYTHON_PATH" >> "$LOG_FILE" 2>&1
    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        echo "✓ Shop $shop_id completed successfully"
        echo "SUCCESS: Shop $shop_id completed successfully" >> "$LOG_FILE"
    elif [ $exit_code -eq 124 ]; then
        echo "⚠ Shop $shop_id timed out"
        echo "TIMEOUT: Shop $shop_id timed out" >> "$LOG_FILE"
    else
        echo "✗ Shop $shop_id failed with exit code $exit_code"
        echo "ERROR: Shop $shop_id failed with exit code $exit_code" >> "$LOG_FILE"
    fi

    return $exit_code
}

# Find all shop workspace directories
echo "Scanning for workspaces..."
echo "Scanning for workspaces..." >> "$LOG_FILE"

WORKSPACES=()
if [ -d "$SHOPEE_SCRIPTS_DIR" ]; then
    for dir in "$SHOPEE_SCRIPTS_DIR"/shop_*; do
        if [ -d "$dir" ]; then
            WORKSPACES+=("$dir")
        fi
    done
fi

if [ ${#WORKSPACES[@]} -eq 0 ]; then
    echo "No workspaces found in $SHOPEE_SCRIPTS_DIR"
    echo "No workspaces found in $SHOPEE_SCRIPTS_DIR" >> "$LOG_FILE"
    rm -f "$PID_FILE"
    exit 0
fi

echo "Found ${#WORKSPACES[@]} workspaces: ${WORKSPACES[*]}"
echo "Found ${#WORKSPACES[@]} workspaces: ${WORKSPACES[*]}" >> "$LOG_FILE"

# Run workspaces in parallel
echo "Starting parallel execution..."
echo "Starting parallel execution..." >> "$LOG_FILE"

SUCCESS_COUNT=0
TOTAL_COUNT=${#WORKSPACES[@]}
PIDS=()

# Start all workspaces in parallel
for workspace in "${WORKSPACES[@]}"; do
    run_workspace "$workspace" &
    PIDS+=($!)
done

# Wait for all processes to complete
for pid in "${PIDS[@]}"; do
    if wait "$pid"; then
        ((SUCCESS_COUNT++))
    fi
done

# Summary
echo "Summary: $SUCCESS_COUNT/$TOTAL_COUNT workspaces completed successfully"
echo "Summary: $SUCCESS_COUNT/$TOTAL_COUNT workspaces completed successfully" >> "$LOG_FILE"
echo "Finished at: $(date)" >> "$LOG_FILE"

# Cleanup
rm -f "$PID_FILE"

if [ $SUCCESS_COUNT -eq $TOTAL_COUNT ]; then
    echo "All workspaces completed successfully"
    echo "All workspaces completed successfully" >> "$LOG_FILE"
    exit 0
else
    echo "Some workspaces failed"
    echo "Some workspaces failed" >> "$LOG_FILE"
    exit 1
fi
