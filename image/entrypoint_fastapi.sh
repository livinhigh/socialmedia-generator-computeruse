#!/bin/bash
set -e

echo "🚀 Starting Social Media Generator "
# echo "Starting X11, VNC, and window manager..."

# # Start X11, VNC, and window manager
# ./start_all.sh || {
#     echo "❌ Failed to start X11 services"
#     exit 1
# }

# echo "✓ X11 services started"

echo "✨ Starting FastAPI backend..."

# Start FastAPI with uvicorn with proper logging
uvicorn socialmedia_generator.fastapi_app:app \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level info \
    --access-log

