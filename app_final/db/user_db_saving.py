# app/recommendation/user_write/user_db_saving.py

import os
import sys
import sqlite3
import json

from app_final.models.user import DB_PATH

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
os.chdir(project_root)
sys.path.append(project_root)

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../app/data/genai.db"))
def save_language_scores(user_id, ielts_score=None, toefl_score=None):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = """
    UPDATE user_data
    SET ielts_score = ?, toefl_score = ?
    WHERE user_id = ?
    """
    cursor.execute(query, (ielts_score, toefl_score, user_id))
    conn.commit()
    conn.close()

def save_academic_chain_results(user_id, subjects, programs):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        subjects_json = json.dumps(subjects)
        programs_json = json.dumps(programs)
        query = """
        INSERT INTO user_academic_chain_results (user_id, matched_subjects, matched_programs)
        VALUES (?, ?, ?)
        """
        cursor.execute(query, (user_id, subjects_json, programs_json))
        conn.commit()
    except Exception as e:
        print(f"ERROR - save_academic_chain_results: {e}")
    finally:
        conn.close()

def save_user_program_selection(user_id, program_id):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = "INSERT INTO user_saved_programs (user_id, program_id) VALUES (?, ?)"
    cursor.execute(query, (user_id, program_id))
    conn.commit()
    conn.close()
