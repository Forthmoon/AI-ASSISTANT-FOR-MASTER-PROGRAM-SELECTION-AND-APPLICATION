from typing import Type, List, Optional
from pydantic import BaseModel, Field, PrivateAttr
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from app_final.project_config import openai_api_key, llm_config
from app_final.recommendation.chains.additional_chain import filter_by_gmat_gre

class AdditionalInput(BaseModel):
    programs: Optional[List] = Field(None, description="List of programs from previous tool")
    country: Optional[str] = Field(None, description="User's country")
    gmat_score: Optional[float] = Field(None, description="User's GMAT score")
    gre_score: Optional[float] = Field(None, description="User's GRE score")

class AdditionalChainTool(BaseTool):
    name: str = "AdditionalChainTool"
    description: str = (
        "Filter programs based on the user's GMAT/GRE scores and nationality."
        "Input: { programs, country, gmat_score, gre_score } (all optional)."
        "Output: JSON format {\"programs\": [...], \"message\": \"...\"}."
    )
    args_schema: Type[BaseModel] = AdditionalInput

    _llm: ChatOpenAI = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._llm = ChatOpenAI(
            temperature=0,
            max_tokens=512,
            model_name=llm_config["model_name"],
            openai_api_key=openai_api_key
        )

    def _run(self, programs: Optional[List] = None, country: Optional[str] = None,
             gmat_score: Optional[float] = None, gre_score: Optional[float] = None) -> str:
        if programs is None or not country:
            return '{"error": "AdditionalChainTool requires a programs list and country."}'
        final_results, msg, _ = filter_by_gmat_gre(
            programs,
            user_country=country,
            user_gmat=gmat_score,
            user_gre=gre_score
        )
        from chatbot_agent.tools.extract_info_tool import USER_MEMORY
        USER_MEMORY["programs"] = final_results
        return f'{{"programs": {final_results}, "message": "{msg}"}}'

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not implemented")

