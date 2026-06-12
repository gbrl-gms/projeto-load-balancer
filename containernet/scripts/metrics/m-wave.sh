#!/bin/bash

DURATION=$1
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

run_wave() {
    /app/wave/run_wave.sh -l sinusoid 10 5 5 20
}

kill_wave() {
    sleep $DURATION
    cleanup
}

cleanup() {
    echo -e "\n[Wrapper] Interrupt signal received. Stopping WAVE..."

    pkill -9 -f "/app/wave/run_wave.sh"
    pkill -9 -f "/app/wave/loadGen/sinusoid/sinusoid.py"
    pkill -9 -f "vlc -I dummy"

    exit 0
}

trap cleanup SIGINT SIGTERM

kill_wave &
run_wave
