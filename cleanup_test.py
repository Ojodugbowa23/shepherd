import sqlite3

conn = sqlite3.connect("church_register.db")
print("before:", conn.execute("select id, full_name, date_joined from members").fetchall())
conn.execute("delete from members where full_name = ?", ("Date Test",))
conn.commit()
print("after:", conn.execute("select id, full_name, date_joined from members").fetchall())
conn.close()