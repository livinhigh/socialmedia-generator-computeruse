#!/bin/bash
# Firefox launcher with display-specific profiles
# Allows Firefox to run simultaneously on multiple displays

# Get the display number from DISPLAY environment variable
DISPLAY_NUM=$(echo $DISPLAY | sed 's/[^0-9]//g')

# Default to display 1 if not set
if [ -z "$DISPLAY_NUM" ]; then
    DISPLAY_NUM=1
fi

# Create profile directory if it doesn't exist
PROFILE_DIR="/tmp/firefox-profile-display${DISPLAY_NUM}"
mkdir -p "$PROFILE_DIR"

# Launch Firefox with display-specific profile
# -no-remote prevents IPC communication with other Firefox instances (required for isolation)
# -profile specifies the profile directory
firefox-esr -no-remote -profile "$PROFILE_DIR" "$@"
