#!/bin/bash

SERVER="${1:-127.0.0.1}"
PORT="${2:-80}"
STREAM_PATH="${3:-/videos/manifest.mpd}"
OUTPUT_DIR="/tmp"
TIMESTAMP_START=$(date +"%Y%m%d_%H%M%S")
CSV_FILE="${OUTPUT_DIR}/dash_${SERVER}-${TIMESTAMP_START}.csv"
BUFFER_LOG="${OUTPUT_DIR}/dash_buffer_${TIMESTAMP_START}.log"
RUNNING=true
VLC_PID=""

mkdir -p "$OUTPUT_DIR"

parse_log_to_csv() {
    local buffer_log="$1"
    
    echo "timestamp,event,segment_number,segment_size_bytes,download_time_ms,buffer_seconds,bandwidth_mbps,http_status,quality_switch" > "$CSV_FILE"
    
    if [ ! -f "$buffer_log" ] || [ ! -s "$buffer_log" ]; then
        echo "Erro: Arquivo de log vazio ou não encontrado." >&2
        return 1
    fi

    local current_segment=""
    local request_time=""
    local response_time=""
    local segment_size=""
    local http_status=""
    local last_quality=""

    while IFS= read -r line; do
        if echo "$line" | grep -q "outgoing request:.*\.m4s"; then
            if date +"%N" | grep -q "N"; then
                request_time="$(date +"%s")000"
            else
                request_time="$(date +"%s%3N")"
            fi
            current_segment=$(echo "$line" | grep -oP 'chunk-stream[0-9]+-\K[0-9]+(?=\.m4s)' || echo "0")
            
        elif echo "$line" | grep -q "incoming response:"; then
            if date +"%N" | grep -q "N"; then
                response_time="$(date +"%s")000"
            else
                response_time="$(date +"%s%3N")"
            fi
            http_status=$(echo "$line" | grep -oP 'HTTP/1\.[01] \K[0-9]+' || echo "0")
            
        elif echo "$line" | grep -q "Content-Length:"; then
            segment_size=$(echo "$line" | grep -oP 'Content-Length: \K[0-9]+' || echo "0")
            
        elif echo "$line" | grep -q "cached.i_time"; then
            local buffer_us=$(echo "$line" | grep -oP 'cached\.i_time \(\K[0-9]+' || echo "0")
            
            local buffer_sec=0
            local download_time=0
            local bandwidth=0
            local quality_switch=0
            
            if command -v bc &> /dev/null; then
                buffer_sec=$(echo "scale=6; $buffer_us / 1000000" | bc 2>/dev/null || echo "0")
                if [ -n "$request_time" ] && [ -n "$response_time" ]; then
                    download_time=$((response_time - request_time))
                fi
                if [ -n "$segment_size" ] && [ "$download_time" != "0" ]; then
                    bandwidth=$(echo "scale=3; ($segment_size * 8) / ($download_time * 1000)" | bc 2>/dev/null || echo "0")
                fi
            else
                buffer_sec=$(( buffer_us / 1000000 ))
                if [ -n "$request_time" ] && [ -n "$response_time" ]; then
                    download_time=$((response_time - request_time))
                fi
                if [ -n "$segment_size" ] && [ "$download_time" != "0" ]; then
                    bandwidth=$(( (segment_size * 8) / (download_time * 1000) ))
                fi
            fi
            
            if [ -n "$segment_size" ] && [ "$segment_size" != "$last_quality" ] && [ -n "$last_quality" ]; then
                quality_switch=1
            fi
            last_quality="$segment_size"
            
            local timestamp=""
            if date +"%N" | grep -q "N"; then
                timestamp="$(date +"%s")000"
            else
                timestamp="$(date +"%s%3N")"
            fi
            
            echo "$timestamp,segment,${current_segment:-0},${segment_size:-0},${download_time:-0},${buffer_sec:-0},${bandwidth:-0},${http_status:-0},${quality_switch:-0}" >> "$CSV_FILE"
            
            current_segment=""
            request_time=""
            response_time=""
            segment_size=""
            http_status=""
            
        elif echo "$line" | grep -qE "download failed|timed out"; then
            local timestamp=""
            if date +"%N" | grep -q "N"; then
                timestamp="$(date +"%s")000"
            else
                timestamp="$(date +"%s%3N")"
            fi
            echo "$timestamp,error,${current_segment:-0},0,0,0,0,0,0" >> "$CSV_FILE"
        fi
    done < "$buffer_log"
}

cleanup() {
    echo ""
    echo "Stopping VLC and parsing results..."

    if [ -n "$VLC_PID" ] && kill -0 "$VLC_PID" 2>/dev/null; then
        kill -15 "$VLC_PID"
        wait "$VLC_PID" 2>/dev/null
    fi
    
    sleep 2

    parse_log_to_csv "$BUFFER_LOG"

    echo "CSV saved: $CSV_FILE"
    echo "Raw log: $BUFFER_LOG"
    echo ""
    echo "To generate JSON summary, run:"
    echo "  ./parse_dash_csv_to_json.sh $CSV_FILE"
    RUNNING=false
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "Collecting MPEG-DASH metrics from ${SERVER}:${PORT}${STREAM_PATH}"
echo "CSV: $CSV_FILE"
echo "Press Ctrl+C to stop..."

STREAM_URL="http://${SERVER}:${PORT}${STREAM_PATH}"

cvlc -I dummy --no-video --no-audio --verbose=2 "$STREAM_URL" > "$BUFFER_LOG" 2>&1 &
VLC_PID=$!

while $RUNNING; do
    if ! kill -0 $VLC_PID 2>/dev/null; then
        echo "VLC process ended"
        parse_log_to_csv "$BUFFER_LOG"
        RUNNING=false
        exit 0
    fi
    sleep 1
done
