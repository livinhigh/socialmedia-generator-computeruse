#!/bin/bash

set -e

# Set default dimensions
export WIDTH=${WIDTH:-1024}
export HEIGHT=${HEIGHT:-768}

# Shared configuration for all startup scripts
export VNC_PORTS="${VNC_PORTS:-5900 5901}"
export NOVNC_PORTS="${NOVNC_PORTS:-}"
export DISPLAY_NUMS="${DISPLAY_NUMS:-}"

# Derive noVNC ports from VNC ports if none were provided
if [ -z "$NOVNC_PORTS" ]; then
    calc_novnc_ports=""
    for port in $VNC_PORTS; do
        calc_novnc_ports+=" $((port + 180))"
    done
    NOVNC_PORTS=${calc_novnc_ports# }
    export NOVNC_PORTS
fi

# Build display numbers from the VNC port list if not provided (1-based)
if [ -z "$DISPLAY_NUMS" ]; then
    calc_display_nums=""
    idx=1
    for _ in $VNC_PORTS; do
        calc_display_nums+=" $idx"
        idx=$((idx + 1))
    done
    DISPLAY_NUMS=${calc_display_nums# }
    export DISPLAY_NUMS
fi

# Basic validation to keep lists aligned
vnc_count=$(echo "$VNC_PORTS" | wc -w)
novnc_count=$(echo "$NOVNC_PORTS" | wc -w)
if [ "$vnc_count" -ne "$novnc_count" ]; then
    echo "Port list mismatch: VNC ports ($vnc_count) vs noVNC ports ($novnc_count)" >&2
    exit 1
fi

# Start Xvfb displays
./xvfb_startup.sh

# Start window managers and utilities for each display in isolated process groups
for DISPLAY_NUM in $DISPLAY_NUMS; do
    (
        export DISPLAY=:${DISPLAY_NUM}
        export DISPLAY_NUM=${DISPLAY_NUM}
        echo "Starting desktop environment for display :${DISPLAY_NUM}"
        ./tint2_startup.sh
        ./mutter_startup.sh
        echo "Desktop environment started for display :${DISPLAY_NUM}"
    ) &
done

# Wait for all display environments to start
wait

# Start VNC servers for all configured displays
./x11vnc_startup.sh

# Start noVNC proxies for all configured displays
./novnc_startup.sh
