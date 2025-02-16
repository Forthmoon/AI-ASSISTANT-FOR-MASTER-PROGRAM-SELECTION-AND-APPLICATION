import os
import sys
import sqlite3
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
app = Flask(
    __name__,
    template_folder=os.path.join(project_root, "templates"),
    static_folder=os.path.join(project_root, "static"),
    static_url_path="/static"
)
app.secret_key = "your_secret_key"
CORS(app)

from app_final.api.auth_api import auth_api
from app_final.api.pdf_api import pdf_api
from app_final.api.application_api import application_api

from langchain_community.chat_models import ChatOpenAI
from app_final.recommendation.chains.integration import integrate_chains
import yaml

from chatbot_agent.tools.extract_info_tool import USER_MEMORY

def load_config(config_path):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

from app_final.project_config import openai_api_key, llm_config, config_data

global_llm = ChatOpenAI(
    temperature=llm_config["temperature"],
    max_tokens=llm_config["max_tokens"],
    model_name=llm_config["model_name"],
    openai_api_key=openai_api_key
)
@app.route("/")
def index():
    return render_template("selections.html")



app.register_blueprint(auth_api)
app.register_blueprint(pdf_api)
app.register_blueprint(application_api)

@app.route("/selections")
def selection():
    return render_template("selections.html")
@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/application_helper")
def application_helper_page():
    return render_template("application_helper.html")

@app.route("/application_overview")
def application_overview_page():
    return render_template("application_overview.html")


@app.route("/api/submit-form", methods=["POST"])
def submit_form():
    try:
        user_input = request.json
        user_id = user_input.get("user_id")
        print(f"Received user_id: {user_id}")
        if not user_id:
            return jsonify({"message": "User not logged in"}), 401

        print("Received data:", user_input)
        user_data = {
            "preferred_subject": user_input.get("preferred_subject"),
            "country": user_input.get("country"),
            "bachelor_major": user_input.get("bachelor_major"),
            "ielts_score": parse_float(user_input.get("ielts_score")),
            "toefl_score": parse_float(user_input.get("toefl_score")),
            "gmat_score": parse_float(user_input.get("gmat_score")),
            "gre_score": parse_float(user_input.get("gre_score")),
        }

        user_preferences = {
            "city_preference": user_input.get("city_preference"),
            "tuition_preference": parse_int(user_input.get("tuition_fee")),
            "duration_preference": parse_int(user_input.get("duration")),
            "qs_preferences": {
                "university_ranking": user_input.get("qs_ranking"),
                "subject_ranking": user_input.get("qs_subject_ranking"),
            }
        }

        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/genai.db"))
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        existing_user = cursor.fetchone()

        if existing_user:
            cursor.execute("""
                UPDATE users
                SET country = ?, bachelor_major = ?, ielts_score = ?, toefl_score = ?, gmat_score = ?, gre_score = ?
                WHERE user_id = ?
            """, (
                user_data["country"], user_data["bachelor_major"],
                user_data["ielts_score"], user_data["toefl_score"],
                user_data["gmat_score"], user_data["gre_score"], user_id
            ))
            print(f"Updated user {user_id}'s data")
        else:
            return jsonify({"message": "User not found in database"}), 404

        conn.commit()

        recommendation_results = integrate_chains(
            conn=conn,
            user_data=user_data,
            user_preferences=user_preferences,
            llm=global_llm
        )

        conn.close()

        max_results = user_input.get("max_results", None)
        if max_results is not None:
            try:
                max_results = int(max_results)
                recommendation_results = recommendation_results[:max_results]
            except ValueError:
                return jsonify({"message": "max_results must be an integer"}), 400

        print("[DEBUG] Final recommendation results:", recommendation_results)
        for idx, rec in enumerate(recommendation_results):
            print(f"[DEBUG] Program {idx} => {rec}")
        return jsonify({"message": "Successfully obtained recommendations", "results": recommendation_results})

    except Exception as e:
        print("Error in /api/submit-form:", e)
        return jsonify({"message": "Data reception failed", "error": str(e)}), 400

@app.route("/api/save-program", methods=["POST"])
def save_program():
    try:
        data = request.json
        user_id = data.get("user_id")
        program_id = data.get("program_id")
        if not user_id or not program_id:
            return jsonify({"message": "Missing user_id or program_id"}), 400

        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/genai.db"))
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM user_saved_programs WHERE user_id = ? AND program_id = ?
        """, (user_id, program_id))
        existing_entry = cursor.fetchone()

        if existing_entry:
            conn.close()
            return jsonify({"message": "Program already saved"}), 200

        cursor.execute("""
            INSERT INTO user_saved_programs (user_id, program_id) VALUES (?, ?)
        """, (user_id, program_id))
        conn.commit()
        conn.close()

        return jsonify({"message": "Program saved successfully!"}), 201

    except Exception as e:
        print("Error saving program:", e)
        return jsonify({"message": "Failed to save program", "error": str(e)}), 500

@app.route("/api/get-saved-programs", methods=["GET"])
def get_saved_programs():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"message": "User ID is required"}), 400

    try:
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/genai.db"))
        print("Database path:", db_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_saved_programs'")
        table_exists = cursor.fetchone()
        if not table_exists:
            print("ERROR: Table `user_saved_programs` does not exist!")
            return jsonify({"message": "Database table not found!"}), 500

        print(f"Querying saved programs for user_id: {user_id}")
        cursor.execute("""
            SELECT p.program_name, u.university
            FROM user_saved_programs usp
            JOIN programs p ON usp.program_id = p.program_id
            JOIN university_info u ON p.university_id = u.university_id
            WHERE usp.user_id = ?
        """, (user_id,))
        saved_programs = [{"program_name": row[0], "university_name": row[1]} for row in cursor.fetchall()]
        print(f"Retrieved {len(saved_programs)} programs")
        conn.close()

        return jsonify({"message": "Saved programs retrieved successfully", "programs": saved_programs})

    except Exception as e:
        print("ERROR in /api/get-saved-programs:", e)
        return jsonify({"message": "Error retrieving saved programs", "error": str(e)}), 500

@app.route("/api/generate-summary-pdf", methods=["GET"])
def generate_summary_pdf():
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/genai.db"))
    try:
        user_id = request.args.get("user_id")
        if not user_id:
            return jsonify({"message": "User ID is required"}), 400

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        import logging
        logging.debug("Connected to database successfully!")

        cursor.execute("""
            SELECT p.university_id, p.program_id
            FROM user_saved_programs usp
            JOIN programs p ON usp.program_id = p.program_id
            WHERE usp.user_id = ?
        """, (user_id,))
        selected_items = [{"university_id": row[0], "program_id": row[1]} for row in cursor.fetchall()]
        conn.close()

        if not selected_items:
            return jsonify({"message": "No saved programs found for this user."}), 404

        from app_final.application_overview.pdf_generator import fetch_multiple_program_details, generate_university_comparison_pdf
        program_data = fetch_multiple_program_details(selected_items)
        pdf_filename = f"user_{user_id}_summary.pdf"
        pdf_path = os.path.join(project_root, "generated_pdfs", pdf_filename)
        generate_university_comparison_pdf(program_data, pdf_path)

        from flask import send_file
        return send_file(pdf_path, as_attachment=True, download_name=pdf_filename, mimetype="application/pdf")

    except Exception as e:
        logging.error(f" ERROR generating PDF: {e}")
        return jsonify({"message": "Error generating summary PDF", "error": str(e)}), 500

# new chatbot api
@app.route("/api/recommendation-chat", methods=["POST"])
def recommendation_chat():
    try:
        data = request.json
        message = data.get("message", "")
        if not message:
            return jsonify({"error": "Empty message"}), 400

        from chatbot_agent.agent import agent as ChatbotAgent
        response_text = ChatbotAgent.run(message)
        return jsonify({
            "response": response_text,
            "programs": USER_MEMORY.get("programs", [])
        })
    except Exception as e:
        print("Error in /api/recommendation-chat:", e)
        return jsonify({"error": str(e)}), 500

print("🔍 Available Routes:")
for rule in app.url_map.iter_rules():
    print(f"{rule}")

def parse_float(val):
    if not val:
        return None
    try:
        return float(val)
    except:
        return None

def parse_bool(val):
    if not val:
        return False
    val_lower = str(val).lower()
    return val_lower in ["yes", "true", "1"]

def parse_int(val):
    if not val:
        return None
    try:
        return int(float(val))
    except ValueError:
        return None

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3000)









