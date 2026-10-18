import sqlite3 
from datetime import date

conn = sqlite3.connect("church_register.db")  # creates the file if it doesn't exist
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys = ON")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        phone_number TEXT NOT NULL,
        status TEXT DEFAULT 'active' NOT NULL,
        photo_path TEXT,
        date_joined TEXT,
        embedding BLOB
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER NOT NULL,
        service_date TEXT NOT NULL,
        method TEXT NOT NULL,
        FOREIGN KEY (member_id) REFERENCES members (id)
    )
""")

conn.commit()
conn.close()

def add_member(name, phone, date_joined=None):
    if date_joined is None:
        date_joined = date.today().isoformat()
    conn = sqlite3.connect("church_register.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO members (full_name, phone_number, date_joined) VALUES (?, ?, ?)",
        (name, phone, date_joined),
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id


def add_attendance(member_id,service_date,method):
    conn = sqlite3.connect("church_register.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO attendance_records (member_id, service_date, method) VALUES (?, ?, ?)",(member_id,service_date,method))
    conn.commit()
    conn.close()

def get_name(member_id):
    conn = sqlite3.connect("church_register.db")
    row = conn.execute("SELECT full_name FROM members WHERE id = ?", (member_id,)).fetchone()
    conn.close()
    return row[0] if row else "unknown"

def get_phone(member_id):
    conn = sqlite3.connect("church_register.db")
    row = conn.execute(
        "SELECT phone_number FROM members WHERE id = ?", (member_id,)
    ).fetchone()
    conn.close()
    return row[0] if row else None

if __name__ == "__main__":
    add_member("Mark Johnson", "08112345678")
    add_attendance(1, "2026-09-20", "manual")