# app/recommendation/prompts/language_prompts.py

from langchain.prompts import PromptTemplate

def alternative_certificate_prompt(alternative_text, user_context):
    """
    Determine whether the user meets the alternative certificate/language exemption criteria.
    """
    template = f"""
The following is a description of an alternative certificate or waiver requirement:
{alternative_text}

The user has the following background:
{user_context}

Based on this, does the user qualify for the exemption or alternative certificate?
Respond with "yes" or "no".
"""
    return template
