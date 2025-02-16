from flask import Blueprint, request, jsonify
import os
from app_final.application_helper.db import get_db_connection  # Connect to the database
from app_final.application_helper.openai_api import ask_openai

application_api = Blueprint("application_api", __name__)

# API endpoint: User uploads a document (existing feature)
@application_api.route("/api/upload-document", methods=["POST"])
def upload_document():
    try:
        data = request.json
        user_id = data.get("user_id")
        document_name = data.get("document_name")
        document_type = data.get("document_type")

        if not user_id or not document_name or not document_type:
            return jsonify({"error": "Missing required fields"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO user_documents (user_id, document_name, document_type) VALUES (?, ?, ?)",
                       (user_id, document_name, document_type))
        conn.commit()
        conn.close()

        return jsonify({"message": "Document uploaded successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# API endpoint: Retrieve uploaded documents of a user (existing feature)
@application_api.route("/api/check-documents", methods=["GET"])
def check_documents():
    try:
        user_id = request.args.get("user_id")

        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT document_name, document_type FROM user_documents WHERE user_id = ?", (user_id,))
        documents = cursor.fetchall()
        conn.close()

        return jsonify({"documents": documents}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# New Chat API
@application_api.route("/api/application/chat", methods=["POST"])
def chat_with_assistant():
    """Processes user input and returns an AI-generated response"""
    try:
        user_input = request.json.get("message", "")
        if not user_input:
            return jsonify({"error": "Empty input"}), 400

        # Calls the AI processing logic, such as LLM
        response_text = ask_openai(user_input)
        return jsonify({"response": response_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# New PDF File Upload API
@application_api.route("/api/application/upload_pdf", methods=["POST"])
def upload_pdf():
    """Handles PDF file uploads"""
    try:
        if "pdf_file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        pdf_file = request.files["pdf_file"]
        file_path = os.path.join("uploaded_pdfs", pdf_file.filename)
        pdf_file.save(file_path)

        # Calls PDF parsing logic if needed
        return jsonify({"message": f"PDF {pdf_file.filename} uploaded successfully."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
