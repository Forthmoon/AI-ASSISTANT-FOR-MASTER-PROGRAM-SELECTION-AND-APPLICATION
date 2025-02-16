import json
from typing import Type, Optional
from pydantic import BaseModel, Field, PrivateAttr
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI

from app_final.project_config import openai_api_key, llm_config
from app_final.recommendation.chains.academic_chain import filter_programs_by_subject_and_major

# Assume this stores global/session memory
from chatbot_agent.tools.extract_info_tool import USER_MEMORY

class AcademicInput(BaseModel):
    preferred_subject: Optional[str] = Field(None, description="User's preferred subject")
    bachelor_major: Optional[str] = Field(None, description="User's bachelor major")

class AcademicChainTool(BaseTool):
    name: str = "AcademicChainTool"
    description: str= (
        "Filter programs based on user's preferred_subject and bachelor_major.\n"
        "Input: { preferred_subject, bachelor_major } (error if any field is missing).\n"
        "On success, returns {\"programs\":[...]}, and writes to USER_MEMORY['programs'].\n"
        "Each entry in the programs array contains {program_id, program_name, university_name}."
    )
    args_schema: Type[BaseModel] = AcademicInput

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
        preferred_subject: Optional[str] = None,
        bachelor_major: Optional[str] = None
    ) -> str:
        # Check required fields
        if not preferred_subject or not bachelor_major:
            return json.dumps(
                {"error": "AcademicChainTool requires both preferred_subject and bachelor_major."}
            )

        # Call backend logic
        results = filter_programs_by_subject_and_major(preferred_subject, bachelor_major, self._llm)
        # Assume results is a list, e.g., [ (program_id, univ_name, subject_id, program_name), ...]
        # or [ (program_id, univ_name, program_name) ...]

        # In AcademicChainTool._run()
        final_programs = []
        for row in results:
            # Assume row is (program_id, univ_name, subj_id, program_name) or (program_id, univ_name, program_name)
            prog_id = row[0]
            univ_name = row[1]
            # If row length is greater than 3, take the fourth item as program_name; otherwise, take the third item
            prog_name = row[3] if len(row) > 3 else row[2]
            final_programs.append({
                "program_id": prog_id,
                "program_name": prog_name,
                "university_name": univ_name
            })

        # Store in global memory
        USER_MEMORY["programs"] = final_programs

        # Return JSON
        return json.dumps({"programs": final_programs}, ensure_ascii=False)

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not implemented")
