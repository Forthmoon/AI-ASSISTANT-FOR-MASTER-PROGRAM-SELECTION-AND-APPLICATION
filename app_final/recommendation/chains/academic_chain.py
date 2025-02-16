import yaml
import json

from app_final.recommendation.prompts.academic_prompts import academic_subject_prompt, bachelor_major_prompt
from app_final.db.db_queries import fetch_subject_list, fetch_programs_by_subject_ids, fetch_bachelor_requirements
# Replace old import
from langchain_openai import ChatOpenAI

# --- Load configuration and initialize LLM ---
def load_config(config_path):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

# academic_chain.py
from app_final.project_config import openai_api_key, llm_config, config_data

# Create a global LLM for Academic Chain GPT calls
global_llm = ChatOpenAI(
    temperature=llm_config["temperature"],
    max_tokens=llm_config["max_tokens"],
    model_name=llm_config["model_name"],
    openai_api_key=openai_api_key
)

# Now openai_api_key, llm_config can be used directly

def check_bachelor_major(user_major, program_major, llm):
    """
    Call GPT to determine if the user's bachelor's major meets the requirements.
    Returns "yes..." / "no..."
    """
    prompt_message = bachelor_major_prompt(user_major, program_major)
    response = llm.invoke(prompt_message)
    return response.content.strip()

def match_subject(user_input, subject_list, llm):
    """
    Use GPT to match user_input to a subject.
    Returns a list such as ["Economics & Econometrics", "Business & Management Studies"].
    """
    try:
        prompt_message = academic_subject_prompt(user_input, subject_list)
        print(f"DEBUG - Subject Matching Prompt:\n{prompt_message}")

        response = llm.invoke(prompt_message)
        print(f"DEBUG - LLM Response:\n{response}")

        response_text = response.content.strip()
        parsed_json = json.loads(response_text)
        matched_subjects = parsed_json.get("subjects", [])

        print(f"DEBUG - Matched Subjects: {matched_subjects}")
        return matched_subjects
    except Exception as e:
        print(f"ERROR - Failed to match subjects: {str(e)}")
        return []

def filter_programs_by_subject_and_major(user_input, user_major, llm):
    """
    1) Retrieve subject_list
    2) Match using GPT => subject_ids
    3) fetch_programs_by_subject_ids => (program_id, program_name, university_name)
    4) GPT determines user_major vs. program_major => filtering
    5) Returns a "4-element" tuple => (program_id, univ_name, subject_id, program_name)

    Note: ranking_chain later unpacks only 4 elements, so avoid adding extra information.
    """
    # Step 1: fetch all subjects
    subject_data = fetch_subject_list()
    print(f"DEBUG - Retrieved Subject Data: {subject_data}")

    subject_mapping = {row[0].strip().lower(): row[1] for row in subject_data}
    subject_list = list(subject_mapping.keys())

    matched_subject_ids = []
    if user_input:
        matched_subs = match_subject(user_input, subject_list, llm)
        for sub in matched_subs:
            lower_sub = sub.strip().lower()
            if lower_sub in subject_mapping:
                matched_subject_ids.append(subject_mapping[lower_sub])

    if not matched_subject_ids:
        print("DEBUG - No matching subject IDs found.")
        return []

    # Step 2: fetch programs
    programs = fetch_programs_by_subject_ids(matched_subject_ids)  # => [(program_id, program_name, university_name), ...]
    print(f"DEBUG - Retrieved Programs: {programs}")

    # Step 3: check user major
    final_results = set()  # Use a set to store unique results

    for (prog_id, prog_name, univ_name) in programs:
        majors = fetch_bachelor_requirements(prog_id)  # e.g. ["Economics", "Business"] ...
        if not majors:
            continue
        major_req = majors[0]
        match_res = check_bachelor_major(user_major, major_req, llm)
        if "yes" in match_res.lower():
            subject_id = matched_subject_ids[0]  # Use only the first matched_subject_id as subject_id
            final_results.add((prog_id, univ_name, subject_id, prog_name))  # ⚡ Use set to remove duplicates

    # Convert back to list
    final_results = list(final_results)

    print(f"DEBUG - Final Academic Results: {final_results}")
    return final_results
