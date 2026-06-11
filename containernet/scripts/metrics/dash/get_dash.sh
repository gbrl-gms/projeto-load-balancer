#!/bin/bash

SERVER="${1:-127.0.0.1}"
PORT="${2:-80}"
STREAM_PATH="${3:-/videos/manifest.mpd}"
OUTPUT_DIR="/tmp"
TIMESTAMP_START=$(date +"%Y%m%d_%H%M%S")
BUFFER_LOG="${OUTPUT_DIR}/dash_buffer_${TIMESTAMP_START}.log"
RUNNING=true
VLC_PID=""

mkdir -p "$OUTPUT_DIR"

cleanup() {
    echo ""
    echo "Stopping VLC and parsing results..."

    if [ -n "$VLC_PID" ] && kill -0 "$VLC_PID" 2>/dev/null; then
        kill -15 "$VLC_PID"
        wait "$VLC_PID" 2>/dev/null

	kill -15 "$XVFB_PID"
	wait "$XVFB_PID" 2>/dev/null
    fi
    
    sleep 2

    echo "Raw log: $BUFFER_LOG"
    echo ""
    echo "To generate JSON summary, run:"
    echo "  ./parse_dash_csv_to_json.sh $CSV_FILE"
    RUNNING=false
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "Collecting MPEG-DASH metrics from ${SERVER}:${PORT}${STREAM_PATH}"
echo "Press Ctrl+C to stop..."

STREAM_URL="http://${SERVER}:${PORT}${STREAM_PATH}"

Xvfb :99 -screen 0 1024x768x24 &
XVFB_PID=$!

export DISPLAY=:99

cvlc -I dummy --no-audio --verbose=2 --vout=xcb_x11 --file-caching=5000 --network-caching=5000 "$STREAM_URL" > "$BUFFER_LOG" 2>&1 &
VLC_PID=$!

while $RUNNING; do
    if ! kill -0 $VLC_PID 2>/dev/null; then
        echo "VLC process ended"
        RUNNING=false
        exit 0
    fi
    sleep 1
done
