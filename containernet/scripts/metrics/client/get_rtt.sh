#!/bin/bash

TARGET="${1:-127.0.0.1}"
TIMESTAMP_START=$(date +"%Y%m%d_%H%M%S")
INTERVAL=1
CSV_FILE="/tmp/ping_${TARGET}-${TIMESTAMP_START}.csv"
RUNNING=true

echo "timestamp,min_ms,avg_ms,max_ms,mdev_ms" > "$CSV_FILE"

cleanup() {
	RUNNING=false
	exit 0
}

trap cleanup SIGINT SIGTERM

while $RUNNING; do
	TIMESTAMP=$(date +"%s%3N")

	echo "PING ATTEMPT"
	PING_OUTPUT=$(ping -c 1 -q "$TARGET" 2>&1)
	PING_EXIT=$?

	if [ $PING_EXIT -eq 0 ]; then
		LAST_LINE=$(echo "$PING_OUTPUT" | tail -1)
		
		if echo "$LAST_LINE" | grep -q '='; then
			VALUES=$(echo "$LAST_LINE" | cut -d'=' -f2 | xargs)
			MIN=$(echo "$VALUES" | cut -d'/' -f1)
			AVG=$(echo "$VALUES" | cut -d'/' -f2)
			MAX=$(echo "$VALUES" | cut -d'/' -f3)
			MDEV=$(echo "$VALUES" | cut -d'/' -f4 | cut -d' ' -f1)
		    
			echo "$TIMESTAMP,$MIN,$AVG,$MAX,$MDEV" >> "$CSV_FILE"
		else
			echo "$TIMESTAMP,0,0,0,0" >> "$CSV_FILE"
			echo "[$TIMESTAMP] PARSE ERROR: $TARGET" >&2
		fi
	else
		echo "$TIMESTAMP,0,0,0,0" >> "$CSV_FILE"
		echo "[$TIMESTAMP] PING FAILED: $TARGET (exit: $PING_EXIT)" >&2
	fi

	sleep $INTERVAL
done
