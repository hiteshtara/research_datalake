import requests, json, logging

def send_slack_alert(webhook_url, title, status, message):
    color = "#36a64f" if status == "SUCCESS" else "#ff0000"
    payload = {
        "attachments": [{
            "fallback": f"{title}: {status}",
            "color": color,
            "title": title,
            "text": message
        }]
    }
    try:
        resp = requests.post(webhook_url, data=json.dumps(payload),
                             headers={'Content-Type': 'application/json'})
        if resp.status_code == 200:
            logging.info(f"Slack alert sent: {status}")
        else:
            logging.error(f"Slack send failed: {resp.text}")
    except Exception as e:
        logging.error(f"Slack error: {e}")
