import csv, os, datetime, socket

def log_runtime_csv(log_dir, runtime_sec, status):
    """Append daily ETL runtime and status to a CSV tracking file."""
    os.makedirs(log_dir, exist_ok=True)
    csv_path = os.path.join(log_dir, "etl_runtime_stats.csv")
    file_exists = os.path.exists(csv_path)

    row = {
        "date": datetime.date.today().isoformat(),
        "hostname": socket.gethostname(),
        "runtime_sec": runtime_sec,
        "runtime_min": round(runtime_sec / 60, 2),
        "status": status
    }

    with open(csv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
    return csv_path
