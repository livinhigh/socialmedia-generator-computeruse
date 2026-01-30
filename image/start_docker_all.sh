#!/bin/bash

set -e

# Check if Docker socket is accessible
if [ ! -e /var/run/docker.sock ]; then
  echo "Error: Docker socket not found at /var/run/docker.sock" >&2
  exit 1
fi

# # Check Docker connectivity
# if ! docker ps > /dev/null 2>&1; then
#   echo "Error: Cannot connect to Docker daemon. Check if Docker is running and socket has correct permissions." >&2
#   exit 1
# fi

# Required environment variables
if [ -z "${ANTHROPIC_API_KEY}" ]; then
  echo "Error: ANTHROPIC_API_KEY is not set" >&2
  exit 1
fi

if [ -z "${GOOGLE_EMAIL}" ]; then
  echo "Error: GOOGLE_EMAIL is not set" >&2
  exit 1
fi

if [ -z "${GOOGLE_PASSWORD}" ]; then
  echo "Error: GOOGLE_PASSWORD is not set" >&2
  exit 1
fi

# Use VNC_PORTS and NOVNC_PORTS from environment variables
VNC_PORTS="${VNC_PORTS}"
NOVNC_PORTS="${NOVNC_PORTS}"

# Build port mapping arguments dynamically from VNC_PORTS and NOVNC_PORTS
PORT_ARGS=""
for port in $VNC_PORTS; do
    PORT_ARGS="${PORT_ARGS} -p ${port}:${port}"
done
for port in $NOVNC_PORTS; do
    PORT_ARGS="${PORT_ARGS} -p ${port}:${port}"
done

# Run sibling Docker container using mounted Docker socket
# The sibling container will execute entrypoint_sibling.sh to set up VNC desktop only (no FastAPI)
echo "Starting sibling Docker container with VNC desktop environment..."
CONTAINER_ID=$(sudo docker run \
  -e ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}" \
  -e GOOGLE_EMAIL="${GOOGLE_EMAIL}" \
  -e GOOGLE_PASSWORD="${GOOGLE_PASSWORD}" \
  -e WIDTH="${WIDTH}" \
  -e HEIGHT="${HEIGHT}" \
  -e DISPLAY_NUMS="${DISPLAY_NUMS}" \
  -e VNC_PORTS="${VNC_PORTS}" \
  -e NOVNC_PORTS="${NOVNC_PORTS}" \
  -v "$(pwd)/computer_use_demo:/home/computeruse/computer_use_demo" \
  -v "${HOME}/.anthropic:/home/computeruse/.anthropic" \
  -v //var/run/docker.sock:/var/run/docker.sock \
  ${PORT_ARGS} \
  -d \
  --entrypoint ./entrypoint_sibling.sh \
  computer-use-demo:local)

echo "Container ID: $CONTAINER_ID"

# Follow logs until we see the success message
echo "Waiting for VNC services to start..."
while true; do
    if sudo docker logs "$CONTAINER_ID" 2>&1 | grep -q "✓ VNC services started"; then
        echo "Sibling Docker container started successfully with VNC desktop environment"
        break
    fi
    sleep 1
done
