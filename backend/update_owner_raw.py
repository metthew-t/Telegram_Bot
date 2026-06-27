import sqlite3

def update_owner():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT id, username, email FROM counselling_user WHERE username='owner'")
    row = cursor.fetchone()
    if row:
        print(f"Found owner: {row}")
        cursor.execute("UPDATE counselling_user SET email='metthewsteferi@gmail.com', email_verified=1 WHERE username='owner'")
        conn.commit()
        print("Updated successfully!")
    else:
        print("Owner not found in db.")
    conn.close()

if __name__ == '__main__':
    update_owner()
