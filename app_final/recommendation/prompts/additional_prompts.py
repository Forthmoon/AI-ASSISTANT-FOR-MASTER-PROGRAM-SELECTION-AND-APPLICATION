# app/recommendation/prompts/additional_prompts.py

from langchain_core.prompts import ChatPromptTemplate

def parse_gmat_gre_notes_prompt(notes, user_country):
    """
    Parse GMAT/GRE requirements:
- Determine whether the user needs to provide GMAT/GRE (based on `notes` and `user_country`)
- Extract the minimum GMAT/GRE score requirement
- Return the result in JSON format:
  {
    "required": true/false,  # Whether GMAT/GRE submission is required
    "min_score": 600,  # Minimum GMAT/GRE score
    "reason": "Only mandatory for non-EU degree holders"
  }
    """
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "You are an AI assistant that analyzes GMAT/GRE requirements for academic programs. "
                  "Extract structured information from the following description."),
        ("user", f"""
Please analyze the following GMAT/GRE admission requirement description:

"{notes}"

The user is from "{user_country}". We need to determine:
1. Whether the user is required to submit GMAT/GRE scores? 
2. If yes, what is the minimum GMAT/GRE score requirement for this user? 
   If both GMAT Focus and GMAT Classic scores are mentioned, we prioritize GMAT Focus.
3. If no minimum score is provided, return `0`.

Respond **ONLY** in the following JSON format **without any extra text**:
{{{{
  "required": true/false,
  "min_score": <int or 0 if not specified>,
  "reason": "<explanation>"
}}}}
""")
    ])

    return prompt_template.format_messages(notes=notes, user_country=user_country)