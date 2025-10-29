#!/bin/bash
#
# Boston University Research Data Lake – Nightly ETL Runner
# ----------------------------------------------------------
# • Runs the nightly ETL job
# • Logs runtime in CSV + SQLite
# • Sends Slack & email notifications
# • Writes a success marker for the watchdog
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
SLACK_WEBHOOK="https://hooks.slack.com/services/XXXX/YYYY/ZZZZ"   # <-- replace with your webhook

# -------- PREPARE ENVIRONMENT --------
cd "$PROJECT_DIR" || {
  echo "$(date): ERROR – cannot cd to $PROJECT_DIR" | /usr/local/bin/sendmail -s "ETL Cron Failure: bad path" $ADMIN_EMAIL
  exit 1
}
if [ ! -f "$PYTHON" ]; then
  echo "$(date): ERROR – venv missing in $VENV_DIR" | /usr/local/bin/sendmail -s "ETL Cron Failure: missing venv" $ADMIN_EMAIL
  exit 1
fi
source "$VENV_DIR/bin/activate"

# -------- START LOG --------
mkdir -p "$LOG_DIR"
echo "----------------------------------------" >> "$LOG_FILE"
echo "$(date): Starting nightly ETL job…" >> "$LOG_FILE"

# -------- RUN ETL --------
start_time=$(date +%s)
$PYTHON src/main.py >> "$LOG_FILE" 2>&1
status=$?
end_time=$(date +%s)
runtime=$((end_time - start_time))
runtime_min=$(awk "BEGIN {print $runtime/60}")

# Determine run status
if [ "$status" -eq 0 ]; then
  run_status="success"
else
  run_status="failure"
fi

# -------- LOG RUNTIME TO CSV --------
$PYTHON - <<END
from src.log_runtime_stats import log_runtime_csv
log_runtime_csv("$LOG_DIR", $runtime, "$run_status")
END

# -------- LOG RUNTIME TO SQLITE --------
$PYTHON - <<END
from src.log_runtime_sqlite import log_runtime_sqlite
log_runtime_sqlite("$LOG_DIR/etl_stats.db", $runtime, "$run_status")
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

  # Slack success message
  send_slack_alert "BU Research Data Lake – ETL Success" \
                   "✅ ETL completed successfully in ${runtime_min} min." \
                   "#36a64f"

else
  echo "$(date): ❌ ETL failed (exit $status)" >> "$LOG_FILE"
  echo "$(date): ETL failed (exit $status)" >> "$STATUS_FILE"

  tail -n 30 "$LOG_FILE" > "$LOG_DIR/last_failure_snippet.txt"

  # Email failure details
  {
    echo "Subject: ETL Cron Job Failure on $(hostname)"
    echo "To: $ADMIN_EMAIL"
    echo "From: noreply@bu.edu"
    echo ""
    echo "ETL failed on $(hostname) at $(date). Exit code: $status"
    echo ""
    echo "Last 30 lines of log:"
    echo "----------------------------------------"
    cat "$LOG_DIR/last_failure_snippet.txt"
    echo "----------------------------------------"
  } | /usr/local/bin/sendmail "$ADMIN_EMAIL"

  # Slack failure message
  send_slack_alert "BU Research Data Lake – ETL Failure" \
                   "❌ ETL failed (exit $status)." \
                   "#ff0000"
  exit 1
fi

echo "$(date): Job finished." >> "$LOG_FILE"
exit 0
