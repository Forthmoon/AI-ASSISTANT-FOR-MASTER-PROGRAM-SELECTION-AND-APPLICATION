import json
from typing import Type, List, Optional
from pydantic import BaseModel, Field, PrivateAttr
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI

from app_final.project_config import openai_api_key, llm_config
from app_final.recommendation.chains.language_chain import filter_programs_by_language

# Assume this also stores global/session memory


class LanguageInput(BaseModel):
    programs: Optional[List] = Field(None, description="List of programs from previous step")
    ielts_score: Optional[float] = Field(None, description="User's IELTS score")
    toefl_score: Optional[float] = Field(None, description="User's TOEFL score")
    alternative_certificate: Optional[str] = Field(None, description="Alternative language cert")

class LanguageChainTool(BaseTool):
    name: str = "LanguageChainTool"
    description: str=(
        "Filter programs based on user's language scores (ielts_score, toefl_score, alternative_certificate).\n"
        "Input: { programs, ielts_score, toefl_score, alternative_certificate }.\n"
        "If programs are not provided, attempt to retrieve from USER_MEMORY['programs']; otherwise, return an error.\n"
        "Output: JSON format {\"programs\":[...]} and update USER_MEMORY['programs']."
    )
    args_schema: Type[BaseModel] = LanguageInput

    _llm: ChatOpenAI = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._llm = ChatOpenAI(
            temperature=0,
            max_tokens=512,
            model_name=llm_config["model_name"],
            openai_api_key=openai_api_key
        )

    def _run(
        self,
        programs: Optional[List] = None,
        ielts_score: Optional[float] = None,
        toefl_score: Optional[float] = None,
        alternative_certificate: Optional[str] = None
    ) -> str:
        # If programs are not provided externally, retrieve from memory
        if not programs:
            if "programs" in USER_MEMORY and USER_MEMORY["programs"]:
                programs = USER_MEMORY["programs"]
            else:
                return json.dumps(
                    {"error": "LanguageChainTool needs a 'programs' list. Please run AcademicChainTool first."}
                )

        # Call the language chain for filtering
        filtered = filter_programs_by_language(
            programs,
            user_ielts=ielts_score,
            user_toefl=toefl_score,
            alt_context=alternative_certificate
        )
        # The filtered result is either a list of dicts or tuples
        # If filter_programs_by_language returns a list of tuples, convert to dicts
        final_programs = []
        for item in filtered:
            if isinstance(item, dict):
                # Already a dict
                final_programs.append(item)
            else:
                # If it's a tuple => (prog_id, univ_name, program_name)...
                prog_id = item[0]
                univ_name = item[1]
                prog_name = item[2] if len(item) > 2 else "unknown"
                final_programs.append({
                    "program_id": prog_id,
                    "program_name": prog_name,
                    "university_name": univ_name
                })

        from chatbot_agent.tools.extract_info_tool import USER_MEMORY
        USER_MEMORY["programs"] = final_programs
        return json.dumps({"programs": final_programs}, ensure_ascii=False)

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not implemented")
