
i#!/bin/bash

SERVER="${1:-127.0.0.1}"
PORT="${2:-5201}"
OUTPUT_DIR="/tmp"
TIMESTAMP_START=$(date +"%Y%m%d_%H%M%S")
JSON_FILE="${OUTPUT_DIR}/iperf_${SERVER}-${TIMESTAMP_START}.json"
RUNNING=true

mkdir -p "$OUTPUT_DIR"

cleanup() {
    echo ""
    echo "Stopping iperf and parsing results..."

    kill $IPERF_PID 2>/dev/null
    wait $IPERF_PID 2>/dev/null

    echo "Raw JSON: $JSON_FILE"
    RUNNING=false
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "Collecting iperf data for $SERVER:$PORT"
echo "Raw JSON: $JSON_FILE"
echo "Press Ctrl+C to stop and generate CSV..."

iperf3 -c "$SERVER" -p "$PORT" -t 0 -J > "$JSON_FILE" 2>&1 &
IPERF_PID=$!

while $RUNNING; do
    if ! kill -0 $IPERF_PID 2>/dev/null; then
        echo "iperf process ended" 
        RUNNING=false
        exit 0
    fi
    sleep 1
done
