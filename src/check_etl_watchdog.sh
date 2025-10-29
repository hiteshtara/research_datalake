#!/bin/bash
#
# Boston University Research Data Lake - ETL Watchdog
# Checks for last successful ETL run and alerts sysadmin if stale or missing.
# Sends alerts via both Email (sendmail) and Slack, including last 30 log lines.
#

# -------- CONFIGURATION --------
PROJECT_DIR="/Users/mukadder/huron/research_datalake"
LOG_DIR="$PROJECT_DIR/logs"
SUCCESS_FILE="$LOG_DIR/last_success.txt"
ETL_LOG_FILE="$LOG_DIR/cron_etl.log"
MAX_AGE_HOURS=26
ADMIN_EMAIL="sysadmin@bu.edu"
SLACK_WEBHOOK="https://hooks.slack.com/services/XXXX/YYYY/ZZZZ"  # replace with your real Slack webhook URL

# -------- FUNCTIONS --------
get_log_tail() {
  if [ -f "$ETL_LOG_FILE" ]; then
    echo "Last 30 lines of ETL log:"
    echo "----------------------------------------"
    tail -n 30 "$ETL_LOG_FILE"
    echo "----------------------------------------"
  else
    echo "ETL log file not found at $ETL_LOG_FILE"
  fi
}

send_email_alert() {
  SUBJECT=$1
  BODY=$2
  LOG_TAIL=$(get_log_tail)

  {
    echo "Subject: $SUBJECT"
    echo "To: $ADMIN_EMAIL"
    echo "From: noreply@bu.edu"
    echo ""
    echo "$BODY"
    echo ""
    echo "Host: $(hostname)"
    echo "Date: $(date)"
    echo ""
    echo "$LOG_TAIL"
  } | /usr/local/bin/sendmail "$ADMIN_EMAIL"
}

send_slack_alert() {
  TITLE=$1
  MESSAGE=$2
  LOG_TAIL=$(get_log_tail)
  COLOR="#ff0000"  # red for alert

  PAYLOAD=$(cat <<EOF
{
  "attachments": [{
    "fallback": "$TITLE",
    "color": "$COLOR",
    "title": "$TITLE",
    "text": "$MESSAGE\n\nHost: $(hostname)\nDate: $(date)\n\n$LOG_TAIL"
  }]
}
EOF
)
  curl -s -X POST -H 'Content-type: application/json' --data "$PAYLOAD" "$SLACK_WEBHOOK" >/dev/null 2>&1
}

# -------- VALIDATION --------
if [ ! -f "$SUCCESS_FILE" ]; then
  SUBJECT="🚨 ETL Watchdog ALERT: Missing success marker"
  BODY="The ETL success marker ($SUCCESS_FILE) was not found.
This usually indicates that the nightly ETL did not run or failed before completion.
Please investigate the cron job or logs at $ETL_LOG_FILE."
  send_email_alert "$SUBJECT" "$BODY"
  send_slack_alert "$SUBJECT" "$BODY"
  exit 1
fi

# Determine file modification time (macOS uses -f; Linux uses -c)
if stat -f %m "$SUCCESS_FILE" >/dev/null 2>&1; then
  FILE_TIME=$(stat -f %m "$SUCCESS_FILE")
else
  FILE_TIME=$(stat -c %Y "$SUCCESS_FILE")
fi

CURRENT_TIME=$(date +%s)
FILE_AGE_HOURS=$(( (CURRENT_TIME - FILE_TIME) / 3600 ))

if [ "$FILE_AGE_HOURS" -gt "$MAX_AGE_HOURS" ]; then
  SUBJECT="⚠️ ETL Watchdog ALERT: Stale success marker"
  BODY="The ETL success marker ($SUCCESS_FILE) is older than $MAX_AGE_HOURS hours.
The ETL may not have run in the past day. Please check cron and ETL logs."
  send_email_alert "$SUBJECT" "$BODY"
  send_slack_alert "$SUBJECT" "$BODY"
  exit 1
fi

# -------- SUCCESS --------
echo "$(date): ✅ Watchdog check passed. ETL last success marker age ${FILE_AGE_HOURS}h." >> "$LOG_DIR/watchdog_status.log"
exit 0
