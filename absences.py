import sqlite3
from datetime import date, timedelta

DB = "church_register.db"


def last_sunday():
    today = date.today()
    return today - timedelta(days=(today.weekday() + 1) % 7)


def sundays_between(start, end):
    day = start + timedelta(days=(6 - start.weekday()) % 7)
    while day <= end:
        yield day
        day += timedelta(days=7)


def find_absences():
    conn = sqlite3.connect(DB)
    members = conn.execute(
        "SELECT id, full_name, date_joined FROM members "
        "WHERE status = 'active' AND date_joined IS NOT NULL"
    ).fetchall()

    absences = []
    end = last_sunday()
    for member_id, name, joined in members:
        rows = conn.execute(
            "SELECT service_date FROM attendance_records WHERE member_id = ?",
            (member_id,),
        )
        present = {row[0] for row in rows}
        for sunday in sundays_between(date.fromisoformat(joined), end):
            if sunday.isoformat() not in present:
                absences.append((member_id, name, sunday.isoformat()))

    conn.close()
    return absences


if __name__ == "__main__":
    for member_id, name, sunday in find_absences():
        print(member_id, name, sunday)