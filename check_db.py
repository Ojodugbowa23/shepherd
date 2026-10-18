import sqlite3

conn = sqlite3.connect("church_register.db")
cur = conn.cursor()

print("members")
for member_id, full_name, status, embedding in cur.execute(
    "SELECT id, full_name, status, embedding FROM members"
):
    size = len(embedding) if embedding else None
    print(member_id, full_name, status, size)

print("attendance_records")
for row in cur.execute(
    "SELECT id, member_id, service_date, method FROM attendance_records"
):
    print(row)

conn.close()