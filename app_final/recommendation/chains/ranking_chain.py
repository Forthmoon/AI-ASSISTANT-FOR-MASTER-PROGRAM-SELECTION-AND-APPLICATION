# app/recommendation/chains/ranking_chain.py

import os
import sys
import json
import yaml
import re

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
os.chdir(project_root)
sys.path.append(project_root)

from app_final.db.db_queries import (
    fetch_university_qs_ranking,
    fetch_subject_qs_ranking,
    get_university_id_from_program,
    get_university_name
)

def parse_qs_ranking_range(qs_ranking_str):
    try:
        qs_str = qs_ranking_str.strip()
        if qs_str.isdigit():
            value = int(qs_str)
            return (value, value)
        if qs_str.lower().startswith("top"):
            parts = qs_str.split()
            value = int(parts[-1])
            return (1, value)
        elif "-" in qs_str:
            parts = qs_str.split("-")
            if len(parts) == 2:
                start = int(parts[0].strip())
                end = int(parts[1].strip())
                return (start, end)
        elif qs_str.lower().startswith("below"):
            parts = qs_str.split()
            value = int(parts[-1])
            return (1, value)
    except Exception as e:
        print(f"[DEBUG] parse_qs_ranking_range error: {e}")
    return (1, 9999)

def sort_programs_by_univ_qs(programs):
    def get_university_rank(univ_id):
        rank_str = fetch_university_qs_ranking(univ_id)
        if rank_str:
            rank_range = parse_qs_ranking_range(rank_str)
            return rank_range[0]
        return 9999
    return sorted(programs, key=lambda x: get_university_rank(x.get("university_id")))

def filter_by_qs_ranking(programs, user_qs_pref):

    print("[DEBUG] Entered filter_by_qs_ranking")
    print("[DEBUG] Received user_qs_pref:", user_qs_pref)
    print("[DEBUG] Received programs list (before filtering):", programs)

    if not user_qs_pref or not programs:
        print("[DEBUG] Ranking chain: No user_qs_pref provided or programs list is empty. Returning original list.")
        new_list = []
        for p in programs:
            new_item = dict(p)
            new_item["qs_ranking"] = None
            new_list.append(new_item)
        return new_list

    uni_rank_str = user_qs_pref.get("university_ranking")
    subj_rank_str = user_qs_pref.get("subject_ranking")
    print(f"[DEBUG] Ranking chain: university_ranking = {uni_rank_str}, subject_ranking = {subj_rank_str}")

    if not uni_rank_str and not subj_rank_str:
        print("[DEBUG] Ranking chain: Neither university_ranking nor subject_ranking provided. Returning original list.")
        new_list = []
        for p in programs:
            new_item = dict(p)
            new_item["qs_ranking"] = None
            new_list.append(new_item)
        return new_list

    uni_range = (1, 9999)
    subj_range = (1, 9999)
    if uni_rank_str:
        uni_range = parse_qs_ranking_range(uni_rank_str)
        print(f"[DEBUG] Ranking chain: Parsed university ranking range: {uni_range}")
    if subj_rank_str:
        subj_range = parse_qs_ranking_range(subj_rank_str)
        print(f"[DEBUG] Ranking chain: Parsed subject ranking range: {subj_range}")

    filtered_programs = []
    for p in programs:
        prog_id = p.get("program_id")
        from app_final.db.db_queries import get_university_id_from_program
        actual_univ_id = get_university_id_from_program(prog_id)
        print(f"[DEBUG] For program_id={prog_id}, actual university id = {actual_univ_id}")
        if actual_univ_id is None:
            print(f"[DEBUG] Skipping program_id={prog_id} because university id is not found")
            continue

        univ_qs = None
        if subj_rank_str and p.get("subject_id"):
            from app_final.db.db_queries import fetch_subject_qs_ranking
            subj_qs = fetch_subject_qs_ranking(actual_univ_id, p.get("subject_id"))
            print(f"[DEBUG] For program_id={prog_id}, fetched subject QS ranking: {subj_qs}")
            if subj_qs:
                subj_start, subj_end = parse_qs_ranking_range(subj_qs)
                print(f"[DEBUG] Parsed subject QS range: ({subj_start}, {subj_end})")
                if not (subj_range[0] <= subj_start <= subj_range[1]):
                    print(f"[DEBUG] Program_id={prog_id} excluded by subject ranking filter")
                    continue

        if uni_rank_str:
            from app_final.db.db_queries import fetch_university_qs_ranking
            univ_qs = fetch_university_qs_ranking(actual_univ_id)
            print(f"[DEBUG] For program_id={prog_id}, fetched university QS ranking: {univ_qs}")
            if univ_qs:
                uni_start, uni_end = parse_qs_ranking_range(univ_qs)
                print(f"[DEBUG] Parsed university QS range: ({uni_start}, {uni_end})")
                if not (uni_range[0] <= uni_start <= uni_range[1]):
                    print(f"[DEBUG] Program_id={prog_id} excluded by university ranking filter")
                    continue

        print(f"[DEBUG] Program_id={prog_id} passed QS ranking filters")
        new_item = dict(p)
        new_item["qs_ranking"] = univ_qs
        filtered_programs.append(new_item)

    print("[DEBUG] Filtered programs before sorting:", filtered_programs)
    filtered_programs.sort(key=lambda x: parse_qs_ranking_range(x["qs_ranking"])[0] if x["qs_ranking"] else 9999)
    print("[DEBUG] Filtered programs after sorting:", filtered_programs)

    from app_final.db.db_queries import get_university_name
    final_list = []
    for p in filtered_programs:
        actual_univ_id = get_university_id_from_program(p.get("id"))
        univ_display_name = get_university_name(actual_univ_id)
        new_item = dict(p)
        new_item["university"] = univ_display_name
        final_list.append(new_item)
    print("[DEBUG] Final returned program list:", final_list)
    return final_list

