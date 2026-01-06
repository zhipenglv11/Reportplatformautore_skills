# backend/database/init_db.py
import sqlite3
from pathlib import Path


def init_db():
    db_path = Path("phase0.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Read SQL file and execute
    sql_file = Path(__file__).parent / "init_sqlite.sql"
    with open(sql_file, "r", encoding="utf-8") as f:
        cursor.executescript(f.read())

    conn.commit()
    conn.close()
    print("Database initialized.")


if __name__ == "__main__":
    init_db()
