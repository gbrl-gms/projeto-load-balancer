#!/bin/bash

SERVER="${1:-127.0.0.1}"
PORT="${2:-5201}"
OUTPUT_DIR="./iperf-metrics"
TIMESTAMP_START=$(date +"%Y%m%d_%H%M%S")
JSON_FILE="${OUTPUT_DIR}/iperf_${SERVER}_${TIMESTAMP_START}.json"
CSV_FILE="${OUTPUT_DIR}/iperf_${SERVER}_${TIMESTAMP_START}.csv"
RUNNING=true

mkdir -p "$OUTPUT_DIR"

parse_json_to_csv() {
    local json_file="$1"
    
    echo "timestamp,server,port,duration_sec,transfer_bytes,bandwidth_bps,bandwidth_mbps,retransmits,cwnd_bytes,jitter_ms,lost_packets" > "$CSV_FILE"
    
    if command -v jq &> /dev/null; then
        local intervals=$(jq -r '.intervals[] | 
            [.sum.start, .sum.end, .sum.bytes, .sum.bits_per_second, .sum.retransmits] | @csv' "$json_file" 2>/dev/null)
        
        if [ ! -z "$intervals" ]; then
            while IFS=',' read -r start end bytes bps retrans; do
                start=$(echo "$start" | tr -d '"')
                end=$(echo "$end" | tr -d '"')
                bytes=$(echo "$bytes" | tr -d '"')
                bps=$(echo "$bps" | tr -d '"')
                retrans=$(echo "$retrans" | tr -d '"')
                
                local mbps=$(echo "scale=2; $bps / 1000000" | bc 2>/dev/null || echo "0")
                local timestamp=$(date -d "@${start%.*}" +"%s%3N" 2>/dev/null || echo "$start")
                
                echo "$timestamp,$SERVER,$PORT,${end%.*},$bytes,$bps,$mbps,$retrans,0,0,0" >> "$CSV_FILE"
            done <<< "$intervals"
        fi
    else
        local bps=$(grep -oP '"bits_per_second":[\d.]+' "$json_file" | tail -1 | grep -oP '[\d.]+')
        local bytes=$(grep -oP '"bytes":\d+' "$json_file" | tail -1 | grep -oP '\d+')
        local retrans=$(grep -oP '"retransmits":\d+' "$json_file" | tail -1 | grep -oP '\d+')
        
        bps=${bps:-0}
        bytes=${bytes:-0}
        retrans=${retrans:-0}
        local mbps=$(echo "scale=2; $bps / 1000000" | bc 2>/dev/null || echo "0")
        
        echo "$(date +"%s%3N"),$SERVER,$PORT,0,$bytes,$bps,$mbps,$retrans,0,0,0" >> "$CSV_FILE"
    fi
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
		echo "iperf process ended unexpectedly" >&2
		parse_json_to_csv "$JSON_FILE"
		RUNNING=false
		exit 1
	fi
sleep 1
done
