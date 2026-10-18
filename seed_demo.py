import sqlite3
from datetime import date, timedelta

import numpy as np

from setup_db import add_attendance, add_member

DB = "church_register.db"

DEMO_MEMBERS = [
    ("Bro Samuel Adeyemi", "08010000001"),
    ("Dcns Grace Okonkwo", "08010000002"),
    ("Elder Joseph Balogun", "08010000003"),
    ("Dcns Ruth Abubakar", "08010000004"),
    ("Bro Daniel Eze", "08010000005"),
    ("Sis Esther Musa", "08010000006"),
    ("Elder Peter Ogunleye", "08010000007"),
    ("Dcns Naomi Bello", "08010000008"),
]
ENROLLED = 5


def last_sunday():
    today = date.today()
    return today - timedelta(days=(today.weekday() + 1) % 7)


def seed_if_empty():
    conn = sqlite3.connect(DB)
    count = conn.execute("SELECT COUNT(*) FROM members").fetchone()[0]
    conn.close()
    if count:
        return False

    start = last_sunday() - timedelta(weeks=5)
    ids = [add_member(name, phone, start.isoformat()) for name, phone in DEMO_MEMBERS]

    rng = np.random.default_rng(7)
    conn = sqlite3.connect(DB)
    for member_id in ids[:ENROLLED]:
        vector = rng.standard_normal(128).astype(np.float32)
        conn.execute("UPDATE members SET embedding = ? WHERE id = ?",
                     (vector.tobytes(), member_id))
    conn.commit()
    conn.close()

    for week in range(6):
        service = (start + timedelta(weeks=week)).isoformat()
        for index, member_id in enumerate(ids):
            if (index + week) % 3 != 0:
                add_attendance(member_id, service, "manual")
    return True


if __name__ == "__main__":
    print("seeded" if seed_if_empty() else "database already has members, nothing changed")