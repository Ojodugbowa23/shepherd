import sqlite3

conn = sqlite3.connect("church_register.db")
conn.execute("ALTER TABLE members ADD COLUMN embedding BLOB")
conn.commit()
conn.close()