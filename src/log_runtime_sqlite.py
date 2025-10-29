import sqlite3, datetime, socket, os

def log_runtime_sqlite(db_path, runtime_sec, status, start_time=None, end_time=None):
    """
    Append daily ETL runtime, timestamps, and status to an SQLite database.
    - db_path: path to SQLite DB file
    - runtime_sec: total runtime in seconds
    - status: 'success' or 'failure'
    - start_time / end_time: string timestamps
    """
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Ensure the correct table schema exists
    cur.execute("""
    CREATE TABLE IF NOT EXISTS etl_runtime (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        hostname TEXT,
        start_time TEXT,
        end_time TEXT,
        runtime_sec REAL,
        runtime_min REAL,
        status TEXT
    )
    """)

    # Insert a new record
    cur.execute("""
    INSERT INTO etl_runtime (date, hostname, start_time, end_time, runtime_sec, runtime_min, status)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.date.today().isoformat(),
        socket.gethostname(),
        start_time,
        end_time,
        runtime_sec,
        round(runtime_sec / 60, 2),
        status
    ))

    conn.commit()
    conn.close()
