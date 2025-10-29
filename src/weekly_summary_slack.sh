#!/bin/bash
#
# BU Research Data Lake - Weekly ETL Summary with Average Runtime
# Parses last 7 days of ETL logs, counts success/failure, and averages runtime.
#

# -------- CONFIGURATION --------
PROJECT_DIR="/Users/mukadder/huron/research_datalake"
LOG_FILE="$PROJECT_DIR/logs/cron_status.log"
SLACK_WEBHOOK="https://hooks.slack.com/services/XXXX/YYYY/ZZZZ"  # Replace with real Slack webhook

# -------- VALIDATION --------
if [ ! -f "$LOG_FILE" ]; then
  echo "$(date): No cron_status.log found at $LOG_FILE"
  exit 1
fi

# -------- EXTRACT DATA (last 7 days) --------
# macOS date syntax (for Linux use: START_DATE=$(date -d '7 days ago' +"%b %e"))
START_DATE=$(date -v-7d +"%b %e")

LAST_WEEK_LOGS=$(awk -v start="$START_DATE" '
BEGIN {found=0}
/[A-Za-z]{3} [ 0-9]{1,2}/ {
  if ($0 ~ start) found=1
}
{ if (found) print }
' "$LOG_FILE")

SUCCESS_COUNT=$(echo "$LAST_WEEK_LOGS" | grep -c "completed successfully")
FAIL_COUNT=$(echo "$LAST_WEEK_LOGS" | grep -c "failed")
TOTAL_RUNS=$((SUCCESS_COUNT + FAIL_COUNT))

# -------- CALCULATE AVERAGE RUNTIME --------
# Extract numeric values after "ETL runtime" (in seconds)
RUNTIMES=$(echo "$LAST_WEEK_LOGS" | grep -oE 'ETL runtime [0-9]+' | awk '{print $3}')

if [ -z "$RUNTIMES" ]; then
  AVG_RUNTIME="N/A"
else
  TOTAL_TIME=0
  COUNT=0
  while read -r val; do
    TOTAL_TIME=$((TOTAL_TIME + val))
    COUNT=$((COUNT + 1))
  done <<< "$RUNTIMES"
  if [ "$COUNT" -gt 0 ]; then
    AVG_RUNTIME=$((TOTAL_TIME / COUNT))
  else
    AVG_RUNTIME="N/A"
  fi
fi

if [ "$TOTAL_RUNS" -eq 0 ]; then
  SUCCESS_RATE="0%"
else
  SUCCESS_RATE=$(( SUCCESS_COUNT * 100 / TOTAL_RUNS ))%
fi

# Convert average runtime seconds → minutes (if numeric)
if [[ "$AVG_RUNTIME" =~ ^[0-9]+$ ]]; then
  AVG_MIN=$(awk "BEGIN {print $AVG_RUNTIME/60}")
else
  AVG_MIN="N/A"
fi
CSV_FILE="$PROJECT_DIR/logs/etl_runtime_stats.csv"
if [ -f "$CSV_FILE" ]; then
  AVG_CSV=$(awk -F, 'NR>1 {sum+=$3; n++} END {if(n>0) print sum/n; else print "N/A"}' "$CSV_FILE")
  AVG_CSV_MIN=$(awk "BEGIN {print $AVG_CSV/60}")
  SUMMARY_MSG="$SUMMARY_MSG\n⏱️ 7-day average runtime (CSV): *${AVG_CSV}s (~${AVG_CSV_MIN} min)*"
fi

# -------- FORMAT MESSAGE --------
SUMMARY_MSG=$(cat <<EOF
📅 *Weekly ETL Summary (Last 7 Days)*

✅ Successful runs: *$SUCCESS_COUNT*
❌ Failed runs: *$FAIL_COUNT*
📈 Success rate: *$SUCCESS_RATE*
⏱️ Average runtime: *$AVG_RUNTIME sec* (~$AVG_MIN min)

Log file: \`$LOG_FILE\`
Host: $(hostname)
EOF
)

PAYLOAD=$(cat <<EOF
{
  "attachments": [{
    "fallback": "Weekly ETL Summary",
    "color": "#439FE0",
    "title": "BU Research Data Lake - Weekly ETL Summary",
    "text": "$SUMMARY_MSG"
  }]
}
EOF
)

# -------- SEND TO SLACK --------
curl -s -X POST -H 'Content-type: application/json' --data "$PAYLOAD" "$SLACK_WEBHOOK" >/dev/null 2>&1

echo "$(date): Weekly summary sent to Slack." >> "$PROJECT_DIR/logs/summary_status.log"
exit 0
