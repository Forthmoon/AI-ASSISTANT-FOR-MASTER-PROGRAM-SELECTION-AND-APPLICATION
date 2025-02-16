from db import cursor, conn

def save_interaction(user_id, question, answer):
    cursor.execute("""
        INSERT INTO Interactions (user_id, question, answer)
        VALUES (?, ?, ?)
    """, (user_id, question, answer))
    conn.commit()
    print("Interaction saved successfully.")
