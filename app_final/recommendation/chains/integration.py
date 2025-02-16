import os
import sys
import yaml
import sqlite3
import json
import re

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from langchain_openai import ChatOpenAI
from app_final.recommendation.chains.academic_chain import filter_programs_by_subject_and_major
from app_final.recommendation.chains.language_chain import filter_programs_by_language
from app_final.recommendation.chains.general_chain import filter_programs_by_general_prefs
from app_final.recommendation.chains.additional_chain import filter_by_gmat_gre
from app_final.recommendation.chains.ranking_chain import filter_by_qs_ranking

def load_config(config_path):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

# academic_chain.py
from app_final.project_config import openai_api_key, llm_config, config_data

global_llm = ChatOpenAI(
    temperature=llm_config["temperature"],
    max_tokens=llm_config["max_tokens"],
    model_name=llm_config["model_name"],
    openai_api_key=openai_api_key
)

def generate_explanation(program, user_data, llm):
    """
    Generate an explanation for the recommended program based on the program details and user data.
    program: (program_id, university_name, subj_id, program_name, qs_ranking)
    To obtain additional details (e.g., tuition_fee, duration, city), query the database.
    """
    # Query the database for general program information (expected format: (tuition_fee, program_duration, city))
    from app_final.db.db_queries import fetch_program_general_info
    DB_PATH = os.path.join(project_root, "data/genai.db")

    try:
        conn = sqlite3.connect(DB_PATH)
        general_info = fetch_program_general_info(conn, program[0])
        conn.close()
    except Exception as e:
        print(f"[DEBUG] Error fetching general info for program {program[0]}: {e}")
        general_info = None
    if general_info:
        tuition_fee, duration, city = general_info
    else:
        tuition_fee, duration, city = "N/A", "N/A", "N/A"

    # Construct prompt by incorporating user data and program details
    prompt = (
        f"User's background: Bachelor's major in {user_data.get('bachelor_major')} and interest in {user_data.get('preferred_subject')}. "
        f"The program '{program[3]}' at '{program[1]}' is located in {city}, has a tuition fee of {tuition_fee}, and lasts {duration} semesters. "
        f"The university's QS ranking is {program[4] if program[4] else 'N/A'}. "
        "Please briefly explain (in one or two concise sentences) why this program is a good fit for the user."
    )
    print(f"[DEBUG] Explanation prompt: {prompt}")
    try:
        response = llm.invoke(prompt)
        explanation = response.content.strip() if response and hasattr(response, "content") else "No explanation available."
        print(f"[DEBUG] Explanation generated: {explanation}")
    except Exception as e:
        explanation = f"Error generating explanation: {e}"
        print(f"[DEBUG] Exception in generate_explanation: {e}")
    return explanation

def integrate_chains(conn, user_data, user_preferences, llm, max_results=None):
    """
    Comprehensive recommendation pipeline: Sequentially calls academic, language, general, additional, and ranking chains,
    then generates a unified explanation for each recommendation.
    """
    subject_and_major_results = filter_programs_by_subject_and_major(
        user_data["preferred_subject"],
        user_data["bachelor_major"],
        llm
    )

    language_results = filter_programs_by_language(
        subject_and_major_results,
        user_data.get("ielts_score"),
        user_data.get("toefl_score"),
        user_data.get("language")
    )

    general_filtered, gen_msg, gen_unmatched = filter_programs_by_general_prefs(
        language_results,
        user_city_pref=user_preferences.get("city_preference"),
        user_tuition_pref=user_preferences.get("tuition_preference"),
        user_duration_pref=user_preferences.get("duration_preference"),
        user_country=user_data.get("country")
    )

    additional_filtered, add_msg, add_unmatched = filter_by_gmat_gre(
        general_filtered,
        user_data.get("country"),
        user_data.get("gmat_score"),
        user_data.get("gre_score"),
    )

    ranking_results = filter_by_qs_ranking(
        additional_filtered,
        user_preferences.get("qs_preferences")
    )

    # Format and finalize each recommended program
    final_results = []
    for program in ranking_results:
        # If the recommended program tuple has fewer than 5 elements, append None (assuming qs_ranking is at index 4)
        if len(program) < 5:
            program = program + (None,)
        explanation = generate_explanation(program, user_data, llm)
        # Append explanation to the tuple, making the final tuple length 6
        final_results.append(program + (explanation,))
    if max_results:
        final_results = final_results[:max_results]
    return final_results
