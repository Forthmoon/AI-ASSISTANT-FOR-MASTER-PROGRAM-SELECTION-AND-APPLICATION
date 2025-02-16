# app/recommendation/chains/general_chain.py

import os
import sqlite3
import sys
import json
import yaml
from langchain_openai import ChatOpenAI
from app_final.recommendation.prompts.general_prompts import (
    parse_general_preferences_prompt,
    match_general_preference_prompt,
    parse_tuition_fee_prompt
)
from app_final.db.db_queries import fetch_program_general_info

from app_final.project_config import openai_api_key, llm_config, config_data

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

def parse_general_preferences(user_input):
    try:
        resp = parse_general_preferences_prompt(user_input)
        content = resp.content.strip()
        data = json.loads(content)
        return {
            "city_preference": data.get("city_preference"),
            "tuition_preference": data.get("tuition_preference"),
            "duration_preference": data.get("duration_preference"),
            "user_country": data.get("country"),
        }
    except Exception as e:
        print(f"[ERROR] parse_general_preferences => {e}")
        return {}

def match_with_openai(program_id, preference_type, db_value, user_value, user_country=None):
    try:
        prompt_str = match_general_preference_prompt(preference_type, db_value, user_value, user_country)
        resp = llm.invoke(prompt_str)
        answer = resp.content.strip().lower()
        print(f"[DEBUG] match_with_openai => pid={program_id}, pref={preference_type}, DB={db_value}, User={user_value}, ans={answer}")
        return (answer == "yes")
    except Exception as e:
        print(f"[ERROR] match_with_openai => {e}")
        return False

def parse_tuition_with_gpt(db_value, user_country):
    try:
        messages = parse_tuition_fee_prompt(db_value, user_country)
        resp = llm.invoke(messages)
        response_text = resp.content.strip() if hasattr(resp, "content") else str(resp).strip()
        print(f"[DEBUG] parse_tuition_with_gpt => GPT output: {repr(response_text)}")
        if not response_text:
            print(f"[ERROR] parse_tuition_with_gpt => Empty response from GPT ")
            return 0
        try:
            cost_value = int(response_text)
        except ValueError:
            print(f"[ERROR] parse_tuition_with_gpt => Invalid cost_value: {response_text}")
            cost_value = 0
        print(f"[DEBUG] Parsed Tuition Fee => Cost: {cost_value}")
        return cost_value
    except Exception as e:
        print(f"[ERROR] parse_tuition_with_gpt => Unexpected error: {e}")
        return 0

def filter_programs_by_general_prefs(programs, user_city_pref=None, user_tuition_pref=None, user_duration_pref=None, user_country=None):
    if not programs:
        return [], "No programs found in the database.", []

    final_results = []
    unmatched = []
    db_path = os.path.join(os.path.dirname(__file__), "../../../data/genai.db")
    conn = sqlite3.connect(db_path)

    for item in programs:
        prog_id = item.get("program_id")
        from app_final.db.db_queries import get_university_id_from_program
        univ_id = get_university_id_from_program(prog_id)
        subj_id = item.get("subject_id")
        row = fetch_program_general_info(conn, prog_id)
        if not row:
            unmatched.append({"id": prog_id, "univ_id": univ_id, "subject_id": subj_id, "error": "No general info found"})
            continue

        tuition_str, dur_str, city_str = row

        city_ok = True
        if user_city_pref:
            city_ok = match_with_openai(prog_id, "city", city_str, user_city_pref, user_country)

        duration_ok = True
        if user_duration_pref is not None:
            try:
                user_duration = int(user_duration_pref)
                duration_ok = match_with_openai(prog_id, "duration", dur_str, user_duration)
            except (ValueError, TypeError):
                duration_ok = False

        tuition_ok = True
        if user_tuition_pref is not None:
            try:
                user_tuition = int(user_tuition_pref)
                cost_val = parse_tuition_with_gpt(tuition_str, user_country)
                tuition_ok = (cost_val == 0 or cost_val <= user_tuition)
            except (ValueError, TypeError):
                tuition_ok = False

        if city_ok and duration_ok and tuition_ok:
            new_item = dict(item)
            new_item["university_id"] = univ_id
            final_results.append(new_item)
        else:
            unmatched.append({"id": prog_id, "univ_id": univ_id, "subject_id": subj_id, "error": "Preferences did not match"})

    conn.close()

    if not final_results:
        return [], "No programs match your preferences", unmatched

    return final_results, f"Found {len(final_results)} matching programs. {len(unmatched)} did not match.", unmatched
