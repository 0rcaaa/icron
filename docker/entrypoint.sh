#!/bin/bash
# Docker entrypoint script for icron with restart signal support.
#
# This script wraps icron and monitors for restart signals.
# When a restart signal is detected, icron is restarted automatically.
# This is used for MCP server installation where icron needs to restart
# to load the newly installed server.

set -e

# Use ICRON_WORKSPACE if set, otherwise default to /app/workspace
WORKSPACE="${ICRON_WORKSPACE:-/app/workspace}"
RESTART_SIGNAL="$WORKSPACE/.restart_signal"

echo "Starting icron with restart signal support..."
echo "Workspace: $WORKSPACE"

while true; do
    echo "$(date): Starting icron..."

    # Run icron gateway and capture exit code
    icron gateway || exit_code=$?

    # Check for restart signal
    if [ -f "$RESTART_SIGNAL" ]; then
        echo "$(date): Restart signal detected"
        cat "$RESTART_SIGNAL"
        echo ""
        echo "Restarting icron..."
        # Signal file is read and cleared by icron on startup
        sleep 1
        continue
    fi

    # Normal exit or error
    echo "$(date): icron exited with code: ${exit_code:-0}"

    # Exit if icron exited normally (code 0) or with error
    exit ${exit_code:-0}
done
