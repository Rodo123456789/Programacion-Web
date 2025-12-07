import sqlite3

conn = sqlite3.connect("base.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
""")

cursor.execute("INSERT INTO usuarios (username, password) VALUES (?, ?)", ("Rodo", "123"))

conn.commit()
conn.close()

print("Base de datos creada y usuario agregado.")
