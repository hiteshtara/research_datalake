🧭 Boston University Research Data Lake – ETL & Monitoring Framework
A complete data automation and monitoring system for Huron Research Suite integrations

Author: Hitesh Tara
Platform: macOS / Linux (tested with Python 3.13.7)
License: MIT (optional — add if desired)

📦 Overview

This repository contains a production-ready ETL framework developed to automate, monitor, and visualize nightly research data integrations for Boston University’s Research Data Lake.

The system ingests data from Huron Research Suite, tracks runtime metrics, logs results, and provides real-time alerts and analytics through Slack, email, and a Flask dashboard.

⚙️ Core Components
Component	Description
🧱 src/cron_runner.sh	Main nightly ETL runner. Executes ETL, logs runtime (start/end), updates SQLite + CSV, and sends Slack/email alerts.
🧩 src/check_etl_watchdog.sh	Watchdog script that runs daily to verify the last ETL run completed successfully. Alerts if missing/stale.
📊 src/app_dashboard.py	Flask web dashboard that visualizes recent ETL runs, runtimes, and statuses with Chart.js and export options.
📈 src/weekly_summary_slack.sh	Posts weekly summaries to Slack (success rate, failures, and average runtime).
💾 src/log_runtime_stats.py	Logs ETL runtime data into logs/etl_runtime_stats.csv.
🧠 src/log_runtime_sqlite.py	Persists runtime metadata in SQLite (logs/etl_stats.db) for dashboards or analytics.
🪄 check_etl_watchdog.sh	Ensures ETL completion; sends email and Slack alerts if the success marker file is missing.
🧰 Directory Structure
research_datalake/
│
├── config/
│   ├── settings.yaml
│   └── modules/
│       ├── irb.yaml
│       └── grants.yaml
│
├── data/
│   ├── incoming/           # Incoming CSVs from Huron
│   ├── raw/                # Preprocessed data
│   ├── staging/            # Cleaned intermediate data
│   ├── curated/            # Final data output
│   └── metadata/manifest.json
│
├── logs/
│   ├── cron_etl.log
│   ├── etl_runtime_stats.csv
│   ├── etl_stats.db
│   ├── last_success.txt
│   ├── summary_status.log
│   └── watchdog_status.log
│
├── src/
│   ├── app_dashboard.py
│   ├── check_etl_watchdog.sh
│   ├── cron_runner.sh
│   ├── weekly_summary_slack.sh
│   ├── log_runtime_stats.py
│   ├── log_runtime_sqlite.py
│   └── main.py
│
├── requirements.txt
├── manage.py
└── README.md

🧠 Features

✅ Fully Automated ETL Pipeline
– Runs nightly via cron, capturing start/end timestamps and runtime duration.

✅ Multi-Destination Logging
– Writes runtime metrics to both CSV and SQLite for redundancy and analytics.

✅ Alerting & Monitoring
– Sends Slack notifications (success & failure) and email alerts (via sendmail).

✅ Flask Dashboard (port 8080)
– Interactive chart of recent runtimes + status table with color-coding and CSV export.

✅ Watchdog Process
– Ensures that ETL jobs run daily; alerts admins if no success marker is found.

✅ Weekly Slack Summary
– Posts 7-day performance report including success/failure counts and average runtime.

✅ Cross-Platform Support
– Works on macOS, Linux, and CI/CD runners using cron.

🚀 Installation & Setup
1️⃣ Clone Repository
git clone git@github.com:hiteshtara/research_datalake.git
cd research_datalake

2️⃣ Create Virtual Environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

3️⃣ Test ETL Locally
bash src/cron_runner.sh


Check generated runtime logs:

cat logs/etl_runtime_stats.csv
sqlite3 logs/etl_stats.db "SELECT * FROM etl_runtime;"

⏰ Crontab Automation

Open your crontab:

crontab -e


Paste the following:

# --- BU Research Data Lake Automation ---
# Run ETL nightly at 2 AM
0 2 * * * /Users/mukadder/huron/research_datalake/src/cron_runner.sh

# Watchdog check at 6 AM
0 6 * * * /Users/mukadder/huron/research_datalake/src/check_etl_watchdog.sh

# Weekly Slack summary every Monday at 7 AM
0 7 * * 1 /Users/mukadder/huron/research_datalake/src/weekly_summary_slack.sh
# ----------------------------------------


Then verify:

crontab -l

🌐 Flask Dashboard

Start the dashboard:

python src/app_dashboard.py


Visit:

http://localhost:8080


Features:

Runtime chart (Chart.js)

Success/failure color-coded table

Start/end timestamps

“Download Full CSV” button

💬 Slack Notifications

To enable Slack alerts:

Create an Incoming Webhook in your Slack workspace.
(Settings → Integrations → Incoming Webhooks → Add New)

Copy the webhook URL.

Update all scripts (cron_runner.sh, check_etl_watchdog.sh, weekly_summary_slack.sh) to include your webhook:

SLACK_WEBHOOK="https://hooks.slack.com/services/XXXX/YYYY/ZZZZ"

📧 Email Alerts (Sendmail)

macOS & Linux users can use /usr/sbin/sendmail directly.
Ensure it exists:

ls /usr/sbin/sendmail


If unavailable, you can remove email lines and rely solely on Slack alerts.

🧩 Logging Examples
CSV Example (logs/etl_runtime_stats.csv)
date,hostname,start_time,end_time,runtime_sec,runtime_min,status
2025-11-04,Hiteshs-iMac,2025-11-04 02:00:00,2025-11-04 02:02:15,135,2.25,success

SQLite Example
SELECT date, start_time, end_time, runtime_min, status FROM etl_runtime ORDER BY id DESC;

🧠 Troubleshooting
Issue	Fix
pandas.errors.ParserError in dashboard	Delete logs/etl_runtime_stats.csv (old schema) and rerun ETL.
sendmail: No such file	Use /usr/sbin/sendmail instead of /usr/local/bin/sendmail.
Slack alerts not posting	Recheck your webhook URL and ensure network access.
Dashboard shows “No data yet”	Run the ETL manually once to create the CSV file.
🧾 Example Slack Messages
✅ Success

BU Research Data Lake – ETL Success
✅ ETL completed successfully in 2.25 min
Start: 2025-11-04 02:00:00
End: 2025-11-04 02:02:15

❌ Failure

BU Research Data Lake – ETL Failure
❌ Exit code: 1
Check logs: /Users/mukadder/huron/research_datalake/logs/cron_etl.log

📊 Weekly Slack Summary

Automatically posts every Monday 7 AM:

📅 Weekly ETL Summary (Last 7 Days)
✅ Successful runs: 6
❌ Failed runs: 1
⏱️ Avg runtime: 2.35 min
Success rate: 86%

🧠 Future Enhancements

Add date-range filter and pie charts to Flask dashboard.

Integrate AWS S3 for long-term archival of ETL logs.

Add REST API endpoints for ETL metrics (for external dashboards).

Convert Slack summaries to HTML/PDF reports.

👏 Acknowledgments

Developed by Hitesh Tara, leveraging open-source Python tools:
Flask, pandas, sqlite3, Chart.js, requests, and native Linux cron automation.

📜 License

You can optionally include an MIT license:

MIT License

Copyright (c) 2025 Hitesh Tara

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the “Software”), to deal
in the Software without restriction...