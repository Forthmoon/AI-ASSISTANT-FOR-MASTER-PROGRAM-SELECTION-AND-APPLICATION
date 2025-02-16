# app_final/db/db_schema.py
import os
import sqlite3

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
DB_PATH = os.path.join(project_root, "data", "genai.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn

def get_database_schema() -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    schema_lines = []
    for tbl in tables:
        table_name = tbl[0]
        if table_name.startswith("sqlite_"):
            continue
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        col_str = ", ".join([f"{col[1]} ({col[2]})" for col in columns])
        schema_lines.append(f"Table: {table_name}, Columns: {col_str}")
    conn.close()

    return "\n".join(schema_lines)
