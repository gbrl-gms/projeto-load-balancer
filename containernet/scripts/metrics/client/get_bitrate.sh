
i#!/bin/bash

SERVER="${1:-127.0.0.1}"
PORT="${2:-5201}"
OUTPUT_DIR="/tmp"
TIMESTAMP_START=$(date +"%Y%m%d_%H%M%S")
JSON_FILE="${OUTPUT_DIR}/iperf_${SERVER}-${TIMESTAMP_START}.json"
CSV_FILE="${OUTPUT_DIR}/iperf_${SERVER}-${TIMESTAMP_START}.csv"
RUNNING=true

mkdir -p "$OUTPUT_DIR"

parse_json_to_csv() {
    local json_file="$1"
    
    echo "timestamp,server,port,duration_sec,transfer_bytes,bandwidth_bps,bandwidth_mbps,retransmits,cwnd_bytes,jitter_ms,lost_packets" > "$CSV_FILE"
    
    if [ ! -f "$json_file" ] || [ ! -s "$json_file" ]; then
        echo "Erro: Arquivo JSON vazio ou não encontrado." >&2
        return 1
    fi

    local bps=$(awk -F: '/"bits_per_second":/ {gsub(/[ ,]/, "", $2); val=$2} END {print val}' "$json_file")
    local bytes=$(awk -F: '/"bytes":/ {gsub(/[ ,]/, "", $2); val=$2} END {print val}' "$json_file")
    local retrans=$(awk -F: '/"retransmits":/ {gsub(/[ ,]/, "", $2); val=$2} END {print val}' "$json_file")
    
    bps=${bps:-0}
    bytes=${bytes:-0}
    retrans=${retrans:-0}
    
    local mbps=0
    if command -v bc &> /dev/null; then
        mbps=$(echo "scale=2; $bps / 1000000" | bc 2>/dev/null || echo "0")
    else
        mbps=$(( bps / 1000000 ))
    fi
    
    local timestamp=""
    if date +"%N" | grep -q "N"; then
        timestamp="$(date +"%s")000"
    else
        timestamp="$(date +"%s%3N")"
    fi
    
    echo "$timestamp,$SERVER,$PORT,0,$bytes,$bps,$mbps,$retrans,0,0,0" >> "$CSV_FILE"
}

cleanup() {
    echo ""
    echo "Stopping iperf and parsing results..."

    kill $IPERF_PID 2>/dev/null
    wait $IPERF_PID 2>/dev/null

    parse_json_to_csv "$JSON_FILE"

    echo "CSV saved: $CSV_FILE"
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
        parse_json_to_csv "$JSON_FILE"
        RUNNING=false
        exit 0
    fi
    sleep 1
done
