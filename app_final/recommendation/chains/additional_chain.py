import os
import sqlite3
import json
import yaml
from langchain_openai import ChatOpenAI

from app_final.recommendation.prompts.additional_prompts import parse_gmat_gre_notes_prompt
from app_final.db.db_queries import fetch_gmat_gre_requirements
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

def filter_by_gmat_gre(programs, user_country, user_gmat=None, user_gre=None):
    if not programs:
        return [], "No programs found in the database.", []

    db_path = os.path.join(os.path.dirname(__file__), "../../../data/genai.db")
    conn = sqlite3.connect(db_path)
    final_results = []
    unmatched_programs = []

    print("\n[DEBUG] Starting GMAT/GRE filtering...")

    for program in programs:
        prog_id = program.get("program_id")
        print(f"\n[DEBUG] Processing Program ID: {prog_id}")

        gmat_gre_info = fetch_gmat_gre_requirements(conn, prog_id)
        if not gmat_gre_info:
            print(f"[DEBUG] Program {prog_id}: No GMAT/GRE requirement, passing through")
            final_results.append(program)
            continue

        _, gmat_gre, notes = gmat_gre_info

        gmat_gre_str = "gmat"

        prompt = parse_gmat_gre_notes_prompt(notes, user_country)
        response = llm.invoke(prompt)
        try:
            response_text = response.content.strip()
            print(f"[DEBUG] OpenAI Response for Program {prog_id}: {response_text}")
            if not response_text:
                print(f"[ERROR] Program {prog_id}: Empty response")
                unmatched_programs.append({"id": prog_id, "error": "Empty LLM response"})
                continue
            try:
                parsed_result = json.loads(response_text)
            except json.JSONDecodeError as e:
                print(f"[ERROR] Program {prog_id}: JSON parsing failed - {e}")
                print(f"[DEBUG] Raw OpenAI Response: {response_text}")
                unmatched_programs.append({"id": prog_id, "error": "Invalid JSON format from LLM"})
                continue
        except Exception as e:
            print(f"[ERROR] Program {prog_id}: OpenAI response error - {e}")
            unmatched_programs.append({"id": prog_id, "error": "Error in OpenAI response"})
            continue

        required = parsed_result.get("required", False)
        min_score = parsed_result.get("min_score", 0)
        reason = parsed_result.get("reason", "")
        print(f"[DEBUG] Program {prog_id} - required: {required}, min_score: {min_score}, user_gmat: {user_gmat}, user_gre: {user_gre}")

        if required:
            if gmat_gre_str == "gmat":
                if user_gmat is None:
                    print(f"[DEBUG] Program {prog_id}: GMAT required but not provided")
                    unmatched_programs.append({"id": prog_id, "error": "GMAT required but not provided"})
                    continue
                if user_gmat >= min_score:
                    print(f"[DEBUG] Program {prog_id}: User GMAT score {user_gmat} ≥ {min_score}")
                    final_results.append(program)
                else:
                    print(f"[DEBUG] Program {prog_id}: User GMAT score {user_gmat} < {min_score}")
                    unmatched_programs.append({"id": prog_id, "error": f"GMAT required ({min_score}), user scored {user_gmat}"})
            elif gmat_gre_str == "gre":
                if user_gre is None:
                    print(f"[DEBUG] Program {prog_id}: GRE required but not provided")
                    unmatched_programs.append({"id": prog_id, "error": "GRE required but not provided"})
                    continue
                if user_gre >= min_score:
                    print(f"[DEBUG] Program {prog_id}: User GRE score {user_gre} ≥ {min_score}")
                    final_results.append(program)
                else:
                    print(f"[DEBUG] Program {prog_id}: User GRE score {user_gre} < {min_score}")
                    unmatched_programs.append({"id": prog_id, "error": f"GRE required ({min_score}), user scored {user_gre}"})
        else:
            print(f"[DEBUG] Program {prog_id}: No GMAT/GRE requirement, passing through")
            final_results.append(program)

    conn.close()

    print("\n[DEBUG] GMAT/GRE filtering completed!")
    print(f"[INFO] Programs that passed filtering: {[p.get('id') for p in final_results]}")
    print(f"[INFO] Programs that did not meet requirements: {[p.get('id') for p in unmatched_programs]}")
    if not final_results:
        return [], "No programs matched GMAT/GRE requirements.", unmatched_programs
    return final_results, f"Filtered {len(final_results)} programs based on GMAT/GRE.", unmatched_programs
