from typing import Type, List, Optional
from pydantic import BaseModel, Field, PrivateAttr
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from app_final.project_config import openai_api_key, llm_config
from app_final.recommendation.chains.ranking_chain import filter_by_qs_ranking

class RankingInput(BaseModel):
    programs: Optional[List] = Field(None, description="List of programs from previous tool")
    university_ranking: Optional[str] = Field(None, description="User's university QS ranking preference, e.g. 'Top 100'")
    subject_ranking: Optional[str] = Field(None, description="User's subject QS ranking preference, e.g. 'Below 200'")

class RankingChainTool(BaseTool):
    name: str = "RankingChainTool"
    description: str = (
        "Sort and filter programs based on QS rankings."
        "Input: { programs, university_ranking, subject_ranking } (all optional)."
        "Recognizes phrases like 'high QS ranking schools', 'well-ranked universities', 'top-ranked majors', etc."
        "Output: JSON format {\"programs\": [...]}"
    )
    args_schema: Type[BaseModel] = RankingInput

    _llm: ChatOpenAI = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._llm = ChatOpenAI(
            temperature=0,
            max_tokens=512,
            model_name=llm_config["model_name"],
            openai_api_key=openai_api_key
        )

    def _run(self, programs: Optional[List] = None, university_ranking: Optional[str] = None,
             subject_ranking: Optional[str] = None) -> str:
        if programs is None:
            return '{"error": "RankingChainTool requires a programs list."}'
        qs_pref = {
            "university_ranking": university_ranking,
            "subject_ranking": subject_ranking
        }
        final_results = filter_by_qs_ranking(programs, qs_pref)
        from chatbot_agent.tools.extract_info_tool import USER_MEMORY
        USER_MEMORY["programs"] = final_results
        return f'{{"programs": {final_results}}}'

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not implemented")

