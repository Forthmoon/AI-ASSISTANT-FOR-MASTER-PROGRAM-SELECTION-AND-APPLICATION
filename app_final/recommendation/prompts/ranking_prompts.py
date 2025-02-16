# app/recommendation/prompts/ranking_prompts.py

from langchain.prompts import PromptTemplate

def qs_ranking_parser_prompt(qs_ranking):
    """
    Prompt to parse QS ranking text => minimal & max range
    e.g. "Top 100" => "1-100"
         "101-150" => "101-150"
    """
    template = PromptTemplate(
        input_variables=["qs_ranking"],
        template="""
The QS ranking is: {qs_ranking}.

Parse this ranking into a numeric range "start-end".
Examples:
- "Top 50" => "1-50"
- "Below 100" => "1-100"
- "101-150" => "101-150"

Only output the numeric range, e.g. "1-50".
"""
    )
    return template.format(qs_ranking=qs_ranking)
