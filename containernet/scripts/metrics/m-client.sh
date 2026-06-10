#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: $0 <duration_in_seconds> [target] [port]"
    echo "Example: $0 60 192.168.1.100 5201 (runs for 1 minute)"
    exit 1
fi

DURATION=$1
TARGET="${2:-127.0.0.1}"
PORT="${3:-5201}"
PING_PID=""
IPERF_PID=""
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

cleanup() {
    echo -e "\n[Wrapper] Interrupt signal received. Stopping all collectors..."
    
    if [ -n "$PING_PID" ] && kill -0 "$PING_PID" 2>/dev/null; then
        kill -15 "$PING_PID"
    fi
    
    if [ -n "$IPERF_PID" ] && kill -0 "$IPERF_PID" 2>/dev/null; then
        kill -15 "$IPERF_PID"
    fi

    echo "[Wrapper] All collectors stopped. Exiting."
    exit 0
}

trap cleanup SIGINT SIGTERM

run_collection() {
    local run_time=$1
    local target=$2
    local port=$3

    echo "[Wrapper] Starting ping and iperf metrics collection..."
    echo "[Wrapper] Target: $target | Port: $port"

    $SCRIPT_DIR/client/get_rtt.sh "$target" &
    PING_PID=$!
    
    $SCRIPT_DIR/client/get_bitrate.sh "$target" "$port" &
    IPERF_PID=$!

    echo "[Wrapper] Collectors running in background (Ping PID: $PING_PID | iPerf PID: $IPERF_PID)"
    echo "[Wrapper] Collection will automatically stop in $run_time seconds."

    sleep "$run_time"

    echo "[Wrapper] Time limit reached ($run_time seconds)."
    cleanup
}

run_collection "$DURATION" "$TARGET" "$PORT"
