from typing import Type, List, Optional
from pydantic import BaseModel, Field, PrivateAttr
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from app_final.project_config import openai_api_key, llm_config
from app_final.recommendation.chains.general_chain import filter_programs_by_general_prefs

class GeneralInput(BaseModel):
    programs: Optional[List] = Field(None, description="List of programs from previous tool")
    city_preference: Optional[str] = Field(None, description="User's city preference")
    tuition_fee: Optional[int] = Field(None, description="Maximum tuition fee acceptable")
    duration: Optional[int] = Field(None, description="Preferred program duration in semesters")
    country: Optional[str] = Field(None, description="User's country")

class GeneralChainTool(BaseTool):
    name: str = "GeneralChainTool"
    description: str = (
        "Filter programs based on the user's general preferences such as city (or region in Germany), tuition, and duration."
        "Input: { programs, city_preference, tuition_fee, duration, country } (all optional)."
        "City preference can be a specific city or a region in Germany (e.g., 'Southern Germany')."
        "Output: JSON format {\"programs\": [...], \"message\": \"...\"}."
    )
    args_schema: Type[BaseModel] = GeneralInput

    _llm: ChatOpenAI = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._llm = ChatOpenAI(
            temperature=0,
            max_tokens=512,
            model_name=llm_config["model_name"],
            openai_api_key=openai_api_key
        )

    def _run(self, programs: Optional[List] = None, city_preference: Optional[str] = None,
             tuition_fee: Optional[int] = None, duration: Optional[int] = None,
             country: Optional[str] = None) -> str:
        if programs is None:
            return '{"error": "GeneralChainTool requires a programs list. Please run a previous tool first."}'
        final_results, msg, _ = filter_programs_by_general_prefs(
            programs,
            user_city_pref=city_preference,
            user_tuition_pref=tuition_fee,
            user_duration_pref=duration,
            user_country=country
        )
        from chatbot_agent.tools.extract_info_tool import USER_MEMORY
        USER_MEMORY["programs"] = final_results
        return f'{{"programs": {final_results}, "message": "{msg}"}}'

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not implemented")