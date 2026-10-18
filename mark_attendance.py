import sqlite3
import sys
from datetime import date, timedelta

from matching import shortlist
from setup_db import add_attendance, get_name

DB = "church_register.db"


def last_sunday():
    today = date.today()
    return today - timedelta(days=(today.weekday() + 1) % 7)


def already_marked(member_id, service_date):
    conn = sqlite3.connect(DB)
    row = conn.execute(
        "SELECT 1 FROM attendance_records WHERE member_id = ? AND service_date = ?",
        (member_id, service_date),
    ).fetchone()
    conn.close()
    return row is not None


photo = sys.argv[1]
service_date = last_sunday().isoformat()

candidates = shortlist(photo, k=3)
if not candidates:
    print("No enrolled members to compare against.")
    sys.exit()

print(f"Service date: {service_date}")
for number, (member_id, distance) in enumerate(candidates, start=1):
    print(f"{number}. {get_name(member_id)} (id {member_id}, distance {distance:.2f})")

choice = input("Enter the number of the correct person, or 0 if none: ").strip()
if not choice.isdigit() or not 1 <= int(choice) <= len(candidates):
    print("Nothing recorded.")
    sys.exit()

member_id = candidates[int(choice) - 1][0]
if already_marked(member_id, service_date):
    print(f"{get_name(member_id)} is already marked for {service_date}. Nothing recorded.")
else:
    add_attendance(member_id, service_date, "face_recognition")
    print(f"Recorded {get_name(member_id)} for {service_date}.")