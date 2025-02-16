# app/recommendation/chains/language_chain.py

import os
import sqlite3
import yaml
from langchain_openai import ChatOpenAI
from app_final.recommendation.prompts.language_prompts import alternative_certificate_prompt
from app_final.db.db_queries import fetch_language_requirements_by_program_id

from app_final.project_config import openai_api_key, llm_config


global_llm = ChatOpenAI(
    temperature=llm_config["temperature"],
    max_tokens=llm_config["max_tokens"],
    model_name=llm_config["model_name"],
    openai_api_key=openai_api_key
)

def load_llm(config_path):
    with open(config_path, "r") as file:
        config = yaml.safe_load(file).get("config", {})
    return ChatOpenAI(
        temperature=config["llm"]["temperature"],
        max_tokens=config["llm"]["max_tokens"],
        model_name=config["llm"]["model_name"],
        openai_api_key=config["api_keys"]["openai"],
    )

config_path = os.path.join(os.path.dirname(__file__), "../../../config.yaml")
llm = load_llm(config_path)

def check_alternative_certificate(alternative_text, user_context):
    if not alternative_text:
        print("[DEBUG] No alternative certificate text provided.")
        return False
    prompt_str = alternative_certificate_prompt(alternative_text, user_context)
    try:
        response_text = llm(prompt_str).content.strip()
        print(f"[DEBUG] alternative_certificate => {response_text}")
        return "yes" in response_text.lower()
    except Exception as e:
        print(f"[ERROR] Failed to evaluate alternative certificate: {e}")
        return False

def filter_programs_by_language(academic_chain_programs, user_ielts=None, user_toefl=None, alt_context=None):
    if not academic_chain_programs:
        print("[DEBUG] No academic chain programs provided.")
        return []

    final_results = []
    db_path = os.path.join(os.path.dirname(__file__), "../../../data/genai.db")
    conn = None

    try:
        conn = sqlite3.connect(db_path)
        for item in academic_chain_programs:
            prog_id = item.get("program_id")
            row = fetch_language_requirements_by_program_id(conn, prog_id)
            if not row:
                print(f"[DEBUG] No language requirements found for program_id {prog_id}. Passing program.")
                final_results.append(item)
                continue

            # row => (program_id, program_name, ielts_req, toefl_req, alt_text)
            _, _, req_ielts, req_toefl, alt_text = row

            if req_ielts is None and req_toefl is None:
                print(f"[DEBUG] No IELTS/TOEFL requirements for program_id {prog_id}. Passing.")
                final_results.append(item)
                continue

            ielts_ok = (user_ielts is not None and req_ielts is not None and user_ielts >= req_ielts)
            toefl_ok = (user_toefl is not None and req_toefl is not None and user_toefl >= req_toefl)

            if ielts_ok or toefl_ok:
                print(f"[DEBUG] Program {prog_id} passed based on IELTS/TOEFL scores.")
                final_results.append(item)
            else:
                qualifies = check_alternative_certificate(alt_text, alt_context or "")
                if qualifies:
                    print(f"[DEBUG] Program {prog_id} passed based on alternative certificate.")
                    final_results.append(item)
        # end for
    except sqlite3.Error as e:
        print(f"[ERROR] Database error: {e}")
    finally:
        if conn:
            conn.close()

    return final_results
