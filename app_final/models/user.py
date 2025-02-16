import sqlite3
import hashlib
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "genai.db")


def get_db_connection():
    return sqlite3.connect(DB_PATH)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def login_or_register_user(email, password):
    """Log in the user. If email is not found, register the user automatically."""
    hashed_password = hash_password(password)

    with get_db_connection() as conn:
        cursor = conn.cursor()


        cursor.execute("SELECT user_id, password_hash FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        if user:

            stored_password = user[1]
            if stored_password == hashed_password:
                print("Login successful!")
                return {"message": "Login successful", "user_id": user[0]}, 200
            else:
                return {"message": "Invalid password"}, 401
        else:

            cursor.execute("INSERT INTO users (email, password_hash, created_at, name) VALUES (?, ?, CURRENT_TIMESTAMP, ?)",
               (email, hashed_password, "New User"))

            conn.commit()


            cursor.execute("SELECT user_id FROM Users WHERE email = ?", (email,))
            new_user = cursor.fetchone()

            print("New user registered and logged in!")
            return {"message": "User registered and logged in", "user_id": new_user[0]}, 201


