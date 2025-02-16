import sqlite3
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "genai.db")

# Database connection function
def get_db_connection():
    return sqlite3.connect(DB_PATH)

# Function to fetch program details with university
def get_program_details_with_university(program_name, university_name):
    """Fetch program details including modules, admission requirements, language requirements, and additional conditions."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                p.program_name,
                ui.university,
                p.city,
                p.program_duration,
                COALESCE(p.application_deadline, 'Not Found'),
                COALESCE(p.tuition_fee, 'Not Specified'),
                p.focus,
                COALESCE(ar.bachelor_major, 'Not Specified'),
                COALESCE(ar.completed_ects, 'Not Specified'),
                COALESCE(lr.ielts_score, 'Not Specified'),
                COALESCE(lr.toefl_score, 'Not Specified'),
                COALESCE(lr.german_score, 'Not Specified'),
                COALESCE(lr.alternative_certificate, 'Not Specified'),
                COALESCE(ar.additional_conditions, 'Not Specified')
            FROM programs p
            JOIN university_info ui ON p.university_id = ui.university_id
            LEFT JOIN academic_requirements ar ON p.program_id = ar.program_id
            LEFT JOIN language_requirements lr ON p.program_id = lr.program_id
            WHERE LOWER(p.program_name) LIKE LOWER(?) 
              AND LOWER(ui.university) LIKE LOWER(?)
        """, (f"%{program_name}%", f"%{university_name}%"))

        result = cursor.fetchone()

        if result:
            keys = [
                "Program Name", "University", "City", "Duration",
                "Application Deadline", "Tuition Fee", "Focus",
                "Bachelor Major", "Completed ECTS", "IELTS Score",
                "TOEFL Score", "German Score", "Alternative Certificate",
                "Modules", "Additional Conditions"
            ]
            return dict(zip(keys, result))
        else:
            return None

# Function to get programs by city
def get_programs_by_city(city):
    """Retrieve all programs available in a specific city."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                p.program_name, 
                ui.university, 
                p.city, 
                p.program_duration, 
                COALESCE(p.tuition_fee, 'Not Specified')
            FROM programs p
            JOIN university_info ui ON p.university_id = ui.university_id
            WHERE LOWER(p.city) LIKE LOWER(?)
        """, (f"%{city}%",))
        results = cursor.fetchall()

        if results:
            return [
                {
                    "Program Name": result[0],
                    "University Name": result[1],
                    "City": result[2],
                    "Duration": result[3],
                    "Tuition Fee": result[4]
                }
                for result in results
            ]
        else:
            return []
