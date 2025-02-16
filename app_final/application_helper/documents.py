import sqlite3

# Database connection
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "genai.db")
conn = sqlite3.connect(DB_PATH)  # Update the path if necessary
cursor = conn.cursor()

# Function to upload a document
def upload_document(user_id, document_name, document_type):
    """Upload a document for a user."""
    try:
        cursor.execute("""
            INSERT INTO uploaded_documents (user_id, document_name, document_type)
            VALUES (?, ?, ?)
        """, (user_id, document_name, document_type))
        conn.commit()
        print(f"Document '{document_name}' uploaded successfully.")
    except sqlite3.Error as e:
        print(f"Database error while uploading document: {e}")

# Function to check uploaded documents for a user
def check_documents(user_id):
    """Check uploaded documents for a user."""
    try:
        cursor.execute("SELECT document_name, document_type FROM uploaded_documents WHERE user_id = ?", (user_id,))
        documents = cursor.fetchall()

        if documents:
            print("Uploaded Documents:")
            for doc in documents:
                print(f"Name: {doc[0]}, Type: {doc[1]}")
        else:
            print("No documents uploaded.")
    except sqlite3.Error as e:
        print(f"Database error while checking documents: {e}")

# Example usage
if __name__ == "__main__":
    # Upload a test document
    upload_document(user_id=1, document_name="Transcript.pdf", document_type="transcript")

    # Check uploaded documents for the user
    check_documents(user_id=1)

    # Close the connection after operations
    conn.close()
