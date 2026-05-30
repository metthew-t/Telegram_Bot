import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# List all tables
tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tables:", [t[0] for t in tables])

# Find owner users
try:
    rows = cursor.execute("SELECT username, role FROM counselling_user WHERE role='owner'").fetchall()
    if rows:
        for r in rows:
            print(f"Owner Username: {r[0]} | Role: {r[1]}")
    else:
        print("No owner account found.")
except Exception as e:
    print(f"Error: {e}")

conn.close()
