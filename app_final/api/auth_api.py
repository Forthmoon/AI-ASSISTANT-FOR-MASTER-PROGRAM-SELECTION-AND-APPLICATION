from flask import Flask, request, jsonify, Blueprint, session
from flask_cors import CORS
from app_final.api.user import login_or_register_user  # Import user management function from user.py

auth_api = Blueprint("auth_api", __name__)
CORS(auth_api, supports_credentials=True)  # Allow cross-origin access

# Configure Flask Session (Secret key should be set in recommendation_api.py)
auth_api.secret_key = "your_secret_key"  # Used for session encryption storage

@auth_api.route("/api/login", methods=["POST", "OPTIONS"])
def login():
    if request.method == "OPTIONS":
        print("Handling OPTIONS request")
        return jsonify({"message": "CORS preflight OK"}), 200  # Allow browser to proceed with POST

    try:
        print("Received login request!")  # Terminal should print this
        user_input = request.json
        email = user_input.get("email")
        password = user_input.get("password")

        if not email or not password:
            print("Missing email or password!")
            return jsonify({"message": "Email and password are required"}), 400

        result, status_code = login_or_register_user(email, password)
        if status_code == 200 or status_code == 201:
            from chatbot_agent.tools.extract_info_tool import USER_MEMORY
            USER_MEMORY.clear()
            session["user_id"] = result["user_id"]
            print(f"Login success for {email}")
        else:
            print(f"Login failed: {result}")

        return jsonify(result), status_code

    except Exception as e:
        print("Login Error:", e)
        return jsonify({"message": "Login failed", "error": str(e)}), 500

# Logout API
@auth_api.route("/api/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)  # Clear session
    return jsonify({"message": "Logged out successfully"}), 200
