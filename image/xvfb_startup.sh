#!/bin/bash
set -e  # Exit on error

DPI=96
WIDTH=${WIDTH:-1024}
HEIGHT=${HEIGHT:-768}
RES_AND_DEPTH=${WIDTH}x${HEIGHT}x24

# Use configured display list or default to two displays
DISPLAY_LIST=${DISPLAY_NUMS:-"1 2"}

echo "[xvfb_startup] Starting with DISPLAY_LIST: $DISPLAY_LIST"
echo "[xvfb_startup] WIDTH: $WIDTH, HEIGHT: $HEIGHT"

for DISPLAY_NUM in $DISPLAY_LIST; do
    DISPLAY_VAR=:${DISPLAY_NUM}
    echo "[xvfb_startup] Creating Xvfb on display ${DISPLAY_VAR}"
    
    # Function to check if Xvfb is already running
    check_xvfb_running() {
        if [ -e /tmp/.X${DISPLAY_NUM}-lock ]; then
            return 0  # Xvfb is already running
        else
            return 1  # Xvfb is not running
        fi
    }
    
    # Function to check if Xvfb is ready
    wait_for_xvfb() {
        local timeout=10
        local start_time=$(date +%s)
        while ! DISPLAY=${DISPLAY_VAR} xdpyinfo >/dev/null 2>&1; do
            if [ $(($(date +%s) - start_time)) -gt $timeout ]; then
                echo "Xvfb failed to start within $timeout seconds on display ${DISPLAY_VAR}" >&2
                return 1
            fi
            sleep 0.1
        done
        return 0
    }
    
    # Check if Xvfb is already running
    if check_xvfb_running; then
        echo "Xvfb is already running on display ${DISPLAY_VAR}"
        continue
    fi
    
    echo "Starting Xvfb on display ${DISPLAY_VAR} with resolution ${RES_AND_DEPTH}..."
    
    # Start Xvfb
    Xvfb ${DISPLAY_VAR} -ac -screen 0 $RES_AND_DEPTH -retro -dpi $DPI -nolisten tcp -nolisten unix &
    XVFB_PID=$!
    
    echo "Xvfb process started with PID $XVFB_PID on display ${DISPLAY_VAR}, waiting for readiness..."
    
    # Wait for Xvfb to start
    if wait_for_xvfb; then
        echo "Xvfb started successfully on display ${DISPLAY_VAR}"
        echo "Xvfb PID: $XVFB_PID"
    else
        echo "Xvfb failed to start on display ${DISPLAY_VAR}"
        kill $XVFB_PID 2>/dev/null || true
        exit 1
    fi
done

echo "All Xvfb instances started successfully"
