from datetime import date, timedelta

import sqlite3

from setup_db import add_attendance, add_member

DB = "church_register.db"


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
    ids = [add_member(f"Demo Member {n}", f"080000000{n:02d}", start.isoformat())
           for n in range(1, 9)]
    for week in range(6):
        service = (start + timedelta(weeks=week)).isoformat()
        for index, member_id in enumerate(ids):
            if (index + week) % 3 != 0:
                add_attendance(member_id, service, "manual")
    return True


if __name__ == "__main__":
    print("seeded" if seed_if_empty() else "database already has members, nothing changed")