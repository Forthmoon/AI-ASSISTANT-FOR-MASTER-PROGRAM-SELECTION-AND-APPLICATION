# app/recommendation/prompts/academic_prompts.py

import json
from langchain_core.prompts import ChatPromptTemplate

def academic_subject_prompt(user_input, subject_list):
    """
    Generate a prompt that instructs GPT to output `{"subjects": [...]}`.
    """
    if not user_input or not subject_list:
        raise ValueError("User input and subject list cannot be empty")

    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful AI assistant that matches user input to relevant academic subjects."),
            (
                "user",
                """
User input: "{user_input}"

Available subjects:
{subject_list}

Extract the most relevant subject names from the user input as a valid JSON object.
The JSON must have a top-level key "subjects" whose value is an array of strings. 
If the user mentions multiple subjects, include all of them.

Example output (must be valid JSON):
{{
"subjects": ["Economics & Econometrics", "Business & Management Studies"]
}}
                """
            ),
        ]
    )

    return prompt_template.invoke({
        "user_input": user_input,
        "subject_list": ", ".join(subject_list),
    })

def bachelor_major_prompt(user_major, program_major):
    """
    GPT determines whether the user's bachelor's major meets the program requirements => "yes"/"no" + reason.
    """
    if not user_major or not program_major:
        raise ValueError("User major and program major cannot be empty")

    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", "You are an AI assistant that evaluates academic qualifications."),
            (
                "user",
                """
The user's bachelor's degree: {user_major}.
The program's requirements: {program_major}.
Does the user's degree meet the requirements? Respond "yes" or "no" with a reason.
                """
            ),
        ]
    )

    return prompt_template.invoke({
        "user_major": user_major,
        "program_major": program_major,
    })



