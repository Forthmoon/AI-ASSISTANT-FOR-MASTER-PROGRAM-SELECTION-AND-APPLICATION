# app/recommendation/utils/db_queries.py

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "genai.db")

# Fetch the list of subjects
def fetch_subject_list():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT subject, subject_id FROM subject_info")
    rows = cursor.fetchall()
    conn.close()
    return rows

# Fetch programs by subject IDs
def fetch_programs_by_subject_ids(subject_ids):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    placeholders = ",".join(["?"] * len(subject_ids))
    query = f"""
    SELECT psm.program_id, p.program_name, ui.university
    FROM program_subject_mapping psm
    JOIN programs p ON p.program_id = psm.program_id
    JOIN university_info ui ON ui.university_id = p.university_id
    WHERE psm.subject_id IN ({placeholders})
    """
    cursor.execute(query, subject_ids)
    result = cursor.fetchall()
    conn.close()
    return result

# Fetch bachelor requirements for a given program
def fetch_bachelor_requirements(program_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = "SELECT bachelor_major FROM academic_requirements WHERE program_id=?"
    cursor.execute(query, (program_id,))
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows] if rows else []

# Fetch language requirements by program ID
def fetch_language_requirements_by_program_id(conn, program_id):
    """
    Retrieve the language requirements of a program from the language_requirements table
    and join with the programs table to get the program_name.
    Returns (program_id, program_name, ielts_score, toefl_score, alt_text) or None.
    """
    query = """
    SELECT lr.program_id,
           p.program_name,
           lr.ielts_score,
           lr.toefl_score,
           lr.alternative_certificate
    FROM language_requirements lr
    JOIN programs p ON p.program_id = lr.program_id
    WHERE lr.program_id = ?
    """
    cursor = conn.cursor()
    cursor.execute(query, (program_id,))
    return cursor.fetchone()

# Fetch general program information
def fetch_program_general_info(conn, program_id):
    """
    Return (tuition_fee, program_duration, city)
    """
    query = """
    SELECT tuition_fee, program_duration, city
    FROM programs
    WHERE program_id=?
    """
    cursor = conn.cursor()
    cursor.execute(query, (program_id,))
    return cursor.fetchone()

# Fetch required application documents for a program
def fetch_required_documents(conn, program_id):
    """
    Retrieve required documents for a program including document name,
    whether it is mandatory, and additional notes.
    Returns a list of tuples (doc_name, is_mandatory, notes).
    """
    query = """
    SELECT document_name, is_mandatory, notes
    FROM required_documents
    WHERE program_id=?
    """
    cursor = conn.cursor()
    cursor.execute(query, (program_id,))
    rows = cursor.fetchall()
    return rows

# Fetch QS ranking of a university
def fetch_university_qs_ranking(university_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = "SELECT qs_ranking FROM university_qs_ranking WHERE university_id=?"
    cursor.execute(query, (university_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]  # e.g., "Top 100" or "101-150"
    return None

# Fetch QS ranking for a subject at a university
def fetch_subject_qs_ranking(university_id, subject_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = "SELECT qs_ranking FROM subject_qs_ranking WHERE university_id=? AND subject_id=?"
    cursor.execute(query, (university_id, subject_id))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

# Fetch GMAT/GRE requirements for a program
def fetch_gmat_gre_requirements(conn, program_id):
    """
    Retrieve GMAT/GRE requirements from the program_gmat_gre_requirements table.
    Returns:
    - (program_id, gmat_gre, notes) if required
    - None if no GMAT/GRE requirement exists for the program_id
    """
    query = """
    SELECT program_id, gmat_gre, notes
    FROM program_gmat_gre_requirements
    WHERE program_id = ?
    """
    cursor = conn.cursor()
    cursor.execute(query, (program_id,))
    return cursor.fetchone()

# Get university ID from a program ID
def get_university_id_from_program(program_id):
    """
    Retrieve the university_id for a given program_id from the programs table.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = "SELECT university_id FROM programs WHERE program_id = ?"
    cursor.execute(query, (program_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

# Get university name by university ID
def get_university_name(univ_id):
    """
    Retrieve the university name from the university_info table based on university_id.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = "SELECT university FROM university_info WHERE university_id=?"
    cursor.execute(query, (univ_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

# Database connection context manager
class DBConnection:
    def __enter__(self):
        self.conn = sqlite3.connect(DB_PATH)
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
