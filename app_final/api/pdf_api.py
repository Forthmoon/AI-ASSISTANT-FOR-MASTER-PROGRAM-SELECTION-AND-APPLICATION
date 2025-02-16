from flask import Blueprint, request, jsonify, send_file
from app_final.application_overview.pdf_generator import fetch_multiple_program_details, generate_university_comparison_pdf
import sqlite3
import os

from flask_cors import CORS

pdf_api = Blueprint('pdf_api', __name__)
CORS(pdf_api)  # ✅ 允许跨域访问

# 获取数据库路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/genai.db"))
print(project_root)
print("PDF API 使用的数据库路径:", db_path)


@pdf_api.route("/api/generate-summary-pdf", methods=["GET"])
def generate_summary_pdf():
    try:
        user_id = request.args.get("user_id")

        if not user_id:
            return jsonify({"message": "User ID is required"}), 400

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.university_id, p.program_id
            FROM user_saved_programs usp
            JOIN programs p ON usp.program_id = p.program_id
            WHERE usp.user_id = ?
        """, (user_id,))

        selected_items = [{"university_id": row[0], "program_id": row[1]} for row in cursor.fetchall()]
        conn.close()

        if not selected_items:
            return jsonify({"message": "No saved programs found"}), 404

        data = fetch_multiple_program_details(selected_items)

        if "error" in data:
            return jsonify({"message": "Error fetching program details"}), 500

        # 定义生成的 PDF 文件名及其绝对路径
        pdf_filename = f"user_{user_id}_summary.pdf"
        # 假设你希望将 PDF 存放在 back_side/app/generated_pdfs 目录下
        pdf_dir = os.path.join(project_root, "generated_pdfs")
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)
        pdf_path = os.path.join(pdf_dir, pdf_filename)
        generate_university_comparison_pdf(data, pdf_path)

        return send_file(pdf_path, as_attachment=True, download_name=pdf_filename, mimetype="application/pdf")

    except Exception as e:
        print("❌ ERROR generating PDF:", e)
        return jsonify({"message": "Error generating PDF", "error": str(e)}), 500
