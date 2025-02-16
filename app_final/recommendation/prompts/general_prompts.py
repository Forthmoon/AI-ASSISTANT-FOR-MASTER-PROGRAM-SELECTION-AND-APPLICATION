from langchain_core.prompts import ChatPromptTemplate

def parse_general_preferences_prompt(user_input):
    prompt_template = ChatPromptTemplate.from_messages([
        ("system",
         "You are a helpful AI assistant that extracts user preferences for academic programs."
         ),
        ("user", f"""
Please extract the user's preferences from the following statement. Focus on:
1. Location preference (city or region) in a string format (e.g., "Berlin", "Munich", or "southern Germany").
2. Maximum tuition fee in euros for each semester (convert to an integer value; if not mentioned, return null).
3. Desired program duration in semesters (convert to an integer value; if not mentioned, return null).
4. Identify the user's country of origin.

Respond in JSON format:
{{ 
  "city_preference": "<string or null>",
  "tuition_preference": <int or null>,
  "duration_preference": <int or null>,
  "country": "<string or null>"
}}

User's statement: {user_input}
""")
    ])
    return prompt_template.invoke({})


def match_general_preference_prompt(preference_type, db_value, user_value, user_country=None):
    """
    Generate an OpenAI prompt for evaluating the match of city or program duration.
    Tuition is not handled here (tuition is processed by `parse_tuition_fee_prompt`).
    """
    if preference_type == "tuition":
        return f"""
        You are a precise assistant that evaluates university tuition fees. 
        The university's recorded tuition fee is: "{db_value}".
        The user is from "{user_country}" and has a budget of "{user_value}" euros.
        - If the fee is per semester, compare the numeric value.
        - If the fee is total, treat it as ambiguous.
        Respond only with "yes" or "no".
        """
    elif preference_type == "city":
        return f"""
        The university is located in "{db_value}".
        The user prefers a location: "{user_value}".
        - Consider regional variations and synonyms.
        Respond only with "yes" or "no".
        """
    elif preference_type == "duration":
        return f"""
        The program duration is "{db_value}".
        The user wants a duration of "{user_value}" semesters.
        - If within +/-1 semester, consider it a match.
        Respond only with "yes" or "no".
        """
    else:
        return f"You should respond 'no'."


from langchain_core.prompts import ChatPromptTemplate

def parse_tuition_fee_prompt(db_value, user_country):
    """
    GPT extracts tuition fee information and returns only cost_value (integer).
    """
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "You are an AI assistant that extracts tuition fee details from a university description. "
                   "Your response must contain only a valid integer value."),
        ("user", f"""Analyze the following tuition fee description:
"{db_value}"
User's country: "{user_country}"

Rules:
1) If the description explicitly states 'no tuition' for the user's country, output **only** `0`.
2) If the description provides a **numeric tuition cost per semester**, extract the number and return it.
3) If the description mentions a **total program cost**, but does not specify per semester, return `0` (manual adjustment required).
4) If the tuition fee information is unclear, conflicting, or missing, return `0`.

**Important:**
- Extract only numerical tuition values. Ignore unrelated fees (e.g., administrative fees).
- If different tuition applies to EU vs. non-EU students, extract the relevant cost for the given user.
- If a currency symbol is present (€,$), keep only the numeric value.
- If a range is given (e.g., "€5000-7000 per semester"), use the **lower bound**.
- Convert thousands separators (e.g., "5,000") into plain numbers (e.g., "5000").

**Output Format:**
- Return only a single integer, without any additional text.
Example output:
`1500`
""")
    ])

    return prompt_template.invoke({
        "db_value": db_value,
        "user_country": user_country
    })
