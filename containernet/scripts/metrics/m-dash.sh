#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: $0 <duration_in_seconds> [target] [port] [stream_path]"
    echo "Example: $0 60 192.168.1.100 80 /videos/manifest.mpd (runs for 1 minute)"
    exit 1
fi

DURATION=$1
TARGET="${2:-127.0.0.1}"
PORT="${3:-80}"
STREAM_PATH="${4:-/videos/manifest.mpd}"
DASH_PID=""
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

cleanup() {
    echo -e "\n[Wrapper] Interrupt signal received. Stopping DASH collector..."
    
    if [ -n "$DASH_PID" ] && kill -0 "$DASH_PID" 2>/dev/null; then
        kill -15 "$DASH_PID"
    fi

    echo "[Wrapper] DASH collector stopped. Exiting."
    exit 0
}

trap cleanup SIGINT SIGTERM

run_collection() {
    local run_time=$1
    local target=$2
    local port=$3
    local stream_path=$4

    echo "[Wrapper] Starting MPEG-DASH metrics collection..."
    echo "[Wrapper] Target: $target | Port: $port | Stream: $stream_path"

    $SCRIPT_DIR/dash/get_dash.sh "$target" "$port" "$stream_path" &
    DASH_PID=$!

    echo "[Wrapper] DASH collector running in background (PID: $DASH_PID)"
    echo "[Wrapper] Collection will automatically stop in $run_time seconds."

    sleep "$run_time"

    echo "[Wrapper] Time limit reached ($run_time seconds)."
    cleanup
}

run_collection "$DURATION" "$TARGET" "$PORT" "$STREAM_PATH"
