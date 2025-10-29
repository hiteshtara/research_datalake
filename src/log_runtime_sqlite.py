import sqlite3, datetime, socket, os

def log_runtime_sqlite(db_path, runtime_sec, status):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS etl_runtime (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        hostname TEXT,
        runtime_sec REAL,
        runtime_min REAL,
        status TEXT
    )
    """)

    cur.execute("""
    INSERT INTO etl_runtime (date, hostname, runtime_sec, runtime_min, status)
    VALUES (?, ?, ?, ?, ?)
    """, (
        datetime.date.today().isoformat(),
        socket.gethostname(),
        runtime_sec,
        round(runtime_sec / 60, 2),
        status
    ))

    conn.commit()
    conn.close()
