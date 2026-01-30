#!/bin/bash
set -e

echo "🚀 Starting Sibling Container - VNC Desktop Environment Only"

# Start X11, VNC, and window manager (no FastAPI)
./start_all.sh || {
    echo "❌ Failed to start VNC services"
    exit 1
}

echo "✓ VNC services started"

# Keep the container running
tail -f /dev/null
