import sqlite3

conn = sqlite3.connect("church_register.db")
conn.execute("UPDATE members SET date_joined = ? WHERE id = ?", ("2026-09-20", 1))
conn.commit()
conn.close()