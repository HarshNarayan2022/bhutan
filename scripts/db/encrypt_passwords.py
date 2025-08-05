import os
import psycopg2
import bcrypt
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from backend.scripts.db.session import DATABASE_URL
import traceback


def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def hash_unencrypted_passwords():
    conn = cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Find rows with non-bcrypt passwords (e.g. not starting with $2)
        cursor.execute("""
            SELECT id, user_password 
            FROM user_profiles 
            WHERE user_password NOT LIKE '$2%';
        """)
        users = cursor.fetchall()

        print(f"Found {len(users)} users with unencrypted passwords.")

        for user in users:
            user_id = user['id']
            raw_password = user['user_password']

            # Hash the plaintext password
            hashed_pw = bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt()).decode()

            # Update the row with the hashed password
            cursor.execute("""
                UPDATE user_profiles 
                SET user_password = %s 
                WHERE id = %s
            """, (hashed_pw, user_id))

        conn.commit()
        print("Password hashing complete.")

    except Exception as e:
        print("[ERROR]", e)
        traceback.print_exc()
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    hash_unencrypted_passwords()
