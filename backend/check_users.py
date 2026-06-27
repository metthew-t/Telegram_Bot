import sqlite3

c=sqlite3.connect('db.sqlite3')
res = c.execute("SELECT username, email, email_verified, role FROM counselling_user").fetchall()
for row in res:
    print(row)
