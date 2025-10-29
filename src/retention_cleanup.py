import os, time, logging, shutil, datetime

def purge_old_files(path, retention_days):
    now = time.time()
    cutoff = now - (retention_days * 86400)
    removed = []
    for root, _, files in os.walk(path):
        for f in files:
            full = os.path.join(root, f)
            if os.path.getmtime(full) < cutoff:
                os.remove(full)
                removed.append(full)
    logging.info(f"Purged {len(removed)} old files from {path}")

def archive_curated_data(curated_dir, archive_dir):
    today = datetime.date.today().isoformat()
    archive_path = os.path.join(archive_dir, today)
    os.makedirs(archive_path, exist_ok=True)
    for f in os.listdir(curated_dir):
        src = os.path.join(curated_dir, f)
        dst = os.path.join(archive_path, f)
        shutil.copy2(src, dst)
    logging.info(f"Archived curated files to {archive_path}")
