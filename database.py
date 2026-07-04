import sqlite3 as s
connection = s.connect("events.db")
cursor=connection.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS Events(
    id INTEGER PRIMARY KEY  AUTOINCREMENT,
    event_name TEXT NOT NULL,
    day TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL
)
""")
connection.commit()
connection.close()
print("Database Created")