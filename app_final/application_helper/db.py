import sqlite3
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
db_path = os.path.join(project_root, "data", "genai.db")
print(db_path)

# connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def get_db_connection():
    """返回一个数据库连接"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # 让查询结果以字典形式返回
    return conn

def close_connection():
    conn.close()





