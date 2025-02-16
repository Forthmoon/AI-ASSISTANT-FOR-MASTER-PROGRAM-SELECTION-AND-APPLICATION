import json
from typing import Type
from pydantic import BaseModel, Field, PrivateAttr
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from app_final.project_config import openai_api_key, llm_config

# Global memory for storing structured fields extracted from multi-turn conversations
USER_MEMORY = {
    "country": None,
    "preferred_subject": None,
    "bachelor_major": None,
    "ielts_score": None,
    "toefl_score": None,
    "gmat_score": None,
    "gre_score": None,
    "tuition_fee": None,
    # Additional fields can be added as needed
}


class ExtractUserInfoInput(BaseModel):
    user_input: str = Field(..., description="User's raw message to parse")


class ExtractUserInfoTool(BaseTool):
    name: str = "ExtractUserInfoTool"
    description: str = (
        "Use OpenAI to parse user input and extract fields: country, preferred_subject, "
        "bachelor_major, ielts_score, toefl_score, gmat_score, gre_score, tuition_fee; "
        "Store the extracted results into global memory USER_MEMORY. Input format: { user_input: string }"
    )
    args_schema: Type[BaseModel] = ExtractUserInfoInput

    _llm: ChatOpenAI = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._llm = ChatOpenAI(
            temperature=0,
            max_tokens=512,
            model_name=llm_config["model_name"],  # e.g., "gpt-3.5-turbo-0613"
            openai_api_key=openai_api_key
        )

    def _run(self, user_input: str) -> str:
        extraction_prompt = f"""
        You are an information extraction assistant. Extract the following fields from the user's input.
        If a field is not mentioned, return null:
        - country (string or null)
        - preferred_subject (string or null)
        - bachelor_major (string or null)
        - city_preference (string or null)   # City preference
        - duration (number or null) # Program duration (in semesters)
        - tuition_fee (number or null) # Tuition budget
        - ielts_score (number or null)
        - toefl_score (number or null)
        - gmat_score (number or null)
        - gre_score (number or null)
        - qs_ranking (string or null) # e.g., "Top 100", "Below 200", or null
        - qs_subject_ranking (string or null)

        If the user mentions "southern Germany" or "Munich", set city_preference accordingly. Do not change country.
        Example: "I come from China, want to study in Munich" => "nationality": "China", "city_preference":"Munich"

        Return a valid JSON object. Example:
        {{
          "country": "...",
          "preferred_subject": "...",
          "bachelor_major": "...",
          "city": "Berlin",
          "duration": 4,
          "tuition_fee": 5000,
          "ielts_score": 7.5,
          "toefl_score": null,
          "gmat_score": 680,
          "gre_score": null,
          "qs_ranking": "Top 100",
          "qs_subject_ranking": null
        }}

        User input: {user_input}
        """
        response_msg = self._llm.invoke(extraction_prompt)
        response_text = response_msg.content.strip()
        try:
            parsed_data = json.loads(response_text)
        except json.JSONDecodeError:
            return f"Failed to parse JSON: {response_text}"

        # Update global memory
        for key in USER_MEMORY.keys():
            if key in parsed_data and parsed_data[key] is not None:
                USER_MEMORY[key] = parsed_data[key]

        memory_str = ", ".join(f"{k}={v}" for k, v in USER_MEMORY.items() if v is not None)
        return f"Extracted fields and updated memory: {memory_str}"

    async def _arun(self, user_input: str):
        raise NotImplementedError("Async not implemented")
