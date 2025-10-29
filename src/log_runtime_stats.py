import csv, os, datetime, socket

def log_runtime_csv(log_dir, runtime_sec, status, start_time=None, end_time=None):
    """
    Append daily ETL runtime, timestamps, and status to a CSV tracking file.
    - log_dir: directory for CSV file
    - runtime_sec: total runtime in seconds
    - status: 'success' or 'failure'
    - start_time / end_time: string timestamps
    """
    os.makedirs(log_dir, exist_ok=True)
    csv_path = os.path.join(log_dir, "etl_runtime_stats.csv")
    file_exists = os.path.exists(csv_path)

    # Create a single row of runtime information
    row = {
        "date": datetime.date.today().isoformat(),
        "hostname": socket.gethostname(),
        "start_time": start_time,
        "end_time": end_time,
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
