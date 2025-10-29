#!/bin/bash
#
# Boston University Research Data Lake – Nightly ETL Runner
# ----------------------------------------------------------
# • Runs the nightly ETL job
# • Logs runtime (start & end timestamps)
# • Writes results to CSV and SQLite
# • Sends Slack & email notifications
# • Updates success marker for watchdog
#

# -------- CONFIGURATION --------
PROJECT_DIR="/Users/mukadder/huron/research_datalake"
VENV_DIR="$PROJECT_DIR/venv"
PYTHON="$VENV_DIR/bin/python"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/cron_etl.log"
STATUS_FILE="$LOG_DIR/cron_status.log"
SUCCESS_MARKER="$LOG_DIR/last_success.txt"
ADMIN_EMAIL="sysadmin@bu.edu"
SLACK_WEBHOOK="https://hooks.slack.com/services/XXXX/YYYY/ZZZZ"  # Replace with your Slack webhook

# -------- ENVIRONMENT SETUP --------
cd "$PROJECT_DIR" || {
  echo "$(date): ERROR – cannot cd to $PROJECT_DIR" | /usr/sbin/sendmail -s "ETL Cron Failure: bad path" $ADMIN_EMAIL
  exit 1
}

if [ ! -f "$PYTHON" ]; then
  echo "$(date): ERROR – venv missing in $VENV_DIR" | /usr/sbin/sendmail -s "ETL Cron Failure: missing venv" $ADMIN_EMAIL
  exit 1
fi

source "$VENV_DIR/bin/activate"
mkdir -p "$LOG_DIR"

# -------- START LOGGING --------
echo "----------------------------------------" >> "$LOG_FILE"
echo "$(date): Starting nightly ETL job..." >> "$LOG_FILE"

# -------- RUN ETL --------
start_time_epoch=$(date +%s)
$PYTHON src/main.py >> "$LOG_FILE" 2>&1
status=$?
end_time_epoch=$(date +%s)
runtime=$((end_time_epoch - start_time_epoch))
runtime_min=$(awk "BEGIN {print $runtime/60}")

# Convert epoch to readable timestamps
start_time_fmt=$(date -r $start_time_epoch "+%Y-%m-%d %H:%M:%S")
end_time_fmt=$(date -r $end_time_epoch "+%Y-%m-%d %H:%M:%S")

# Determine run status
if [ "$status" -eq 0 ]; then
  run_status="success"
else
  run_status="failure"
fi

# -------- LOG RUNTIME TO CSV --------
$PYTHON - <<END
from src.log_runtime_stats import log_runtime_csv
log_runtime_csv("$LOG_DIR", $runtime, "$run_status", "$start_time_fmt", "$end_time_fmt")
END

# -------- LOG RUNTIME TO SQLITE --------
$PYTHON - <<END
from src.log_runtime_sqlite import log_runtime_sqlite
log_runtime_sqlite("$LOG_DIR/etl_stats.db", $runtime, "$run_status", "$start_time_fmt", "$end_time_fmt")
END

# -------- SLACK ALERT FUNCTION --------
send_slack_alert() {
  local TITLE="$1"
  local MESSAGE="$2"
  local COLOR="$3"
  local LOG_TAIL
  LOG_TAIL=$(tail -n 20 "$LOG_FILE")
  local PAYLOAD
  read -r -d '' PAYLOAD <<EOF
{
  "attachments": [{
    "fallback": "$TITLE",
    "color": "$COLOR",
    "title": "$TITLE",
    "text": "$MESSAGE\n\nHost: $(hostname)\nDate: $(date)\n\nLast 20 lines of ETL log:\n----------------------------------------\n$LOG_TAIL\n----------------------------------------"
  }]
}
EOF
  curl -s -X POST -H 'Content-type: application/json' --data "$PAYLOAD" "$SLACK_WEBHOOK" >/dev/null 2>&1
}

# -------- HANDLE SUCCESS / FAILURE --------
if [ "$status" -eq 0 ]; then
  echo "$(date): ✅ ETL completed successfully (runtime ${runtime_min} min)" >> "$LOG_FILE"
  echo "$(date): ETL completed successfully" >> "$STATUS_FILE"
  echo "$(date)" > "$SUCCESS_MARKER"

  send_slack_alert "BU Research Data Lake – ETL Success" \
                   "✅ ETL completed successfully in ${runtime_min} min.\nStart: $start_time_fmt\nEnd: $end_time_fmt" \
                   "#36a64f"

else
  echo "$(date): ❌ ETL failed (exit code $status)" >> "$LOG_FILE"
  echo "$(date): ETL failed (exit code $status)" >> "$STATUS_FILE"

  tail -n 30 "$LOG_FILE" > "$LOG_DIR/last_failure_snippet.txt"

  {
    echo "Subject: ETL Cron Job Failure on $(hostname)"
    echo "To: $ADMIN_EMAIL"
    echo "From: noreply@bu.edu"
    echo ""
    echo "ETL job failed on $(hostname) at $(date). Exit code: $status"
    echo ""
    echo "Start time: $start_time_fmt"
    echo "End time:   $end_time_fmt"
    echo "Runtime:    ${runtime_min} minutes"
    echo ""
    echo "Last 30 lines of ETL log:"
    echo "----------------------------------------"
    cat "$LOG_DIR/last_failure_snippet.txt"
    echo "----------------------------------------"
  } | /usr/sbin/sendmail "$ADMIN_EMAIL"

  send_slack_alert "BU Research Data Lake – ETL Failure" \
                   "❌ ETL failed with exit code $status.\nStart: $start_time_fmt\nEnd: $end_time_fmt" \
                   "#ff0000"
  exit 1
fi

echo "$(date): Job finished." >> "$LOG_FILE"
exit 0
