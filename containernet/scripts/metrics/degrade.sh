#!/bin/bash
# senoidal_degradation.sh
# Executar dentro do container
# Uso: ./senoidal_degradation.sh <duração_segundos> [interface]

DURATION="$1"
INTERFACE="${2:-eth0}"

OUTPUT_DIR="/tmp"
TIMESTAMP_START=$(date +"%Y%m%d_%H%M%S")
CSV_FILE="${OUTPUT_DIR}/delay_${TIMESTAMP_START}.csv"

DELAYS=(0 50 100 150 200 250 300)

cleanup() {
    tc qdisc del dev "$INTERFACE" root 2>/dev/null || true
    echo "CSV salvo: $CSV_FILE"
    exit 0
}

trap cleanup SIGINT SIGTERM

tc qdisc add dev "$INTERFACE" root netem delay 0ms 2>/dev/null || true

echo "timestamp_ms,delay_ms" > "$CSV_FILE"

START_TIME=$(date +%s)

while true; do
    ELAPSED=$(($(date +%s) - START_TIME))
    
    [ "$ELAPSED" -ge "$DURATION" ] && cleanup
    
    WAVE_POS=$((ELAPSED % 60))
    
    if [ "$WAVE_POS" -lt 30 ]; then
        INDEX=$((WAVE_POS / 5))
    else
        INDEX=$(((60 - WAVE_POS) / 5))
    fi
    
    CURRENT_DELAY=${DELAYS[$INDEX]}
    
    tc qdisc change dev "$INTERFACE" root netem delay ${CURRENT_DELAY}ms 20ms
    
    TIMESTAMP_MS=$(date +%s%3N 2>/dev/null || echo $(($(date +%s) * 1000)))
    echo "$TIMESTAMP_MS,$CURRENT_DELAY" >> "$CSV_FILE"
    
    sleep 1
done
