# chatbot_agent/agent.py
import os
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI

from chatbot_agent.tools.extract_info_tool import ExtractUserInfoTool, USER_MEMORY
from chatbot_agent.tools.academic_tool import AcademicChainTool
from chatbot_agent.tools.language_tool import LanguageChainTool
from chatbot_agent.tools.general_tool import GeneralChainTool
from chatbot_agent.tools.additional_tool import AdditionalChainTool
from chatbot_agent.tools.ranking_tool import RankingChainTool
from app_final.project_config import openai_api_key, llm_config

llm = ChatOpenAI(
    model_name="gpt-4o-mini",
    temperature=0,
    openai_api_key=openai_api_key
)

memory = ConversationBufferMemory(return_messages=True)

tools = [
    ExtractUserInfoTool(),
    AcademicChainTool(),
    LanguageChainTool(),
    GeneralChainTool(),
    AdditionalChainTool(),
    RankingChainTool()
]

system_prompt =  """
You are a multi-turn conversation assistant equipped with the following tools:
1) ExtractUserInfoTool: Extracts key fields (country, preferred subject, bachelor major, city or region, duration, tuition fee, IELTS, GMAT, GRE, etc.) from user input and updates memory.
2) AcademicChainTool: Use when filtering by subject + bachelor major is required.
3) LanguageChainTool: Use if the user mentions IELTS, TOEFL, or alternative language proficiency requirements.
4) GeneralChainTool: Use if the user mentions a city, region (where they want to study), tuition fee preferences, or program duration (in semesters).
5) AdditionalChainTool: Use if the user mentions GMAT or GRE requirements.
6) RankingChainTool: Use if the user mentions QS university rankings or QS subject rankings.

Follow these rules:
- After each user input, first call ExtractUserInfoTool to parse and update memory fields.
- If the conversation indicates a need for filtering by subject, language, GMAT, or ranking, call the corresponding tool.
- If the user explicitly states "I don't want an MBA" or similar, confirm whether they want to exclude MBA programs in academic filtering.
- If required fields are missing, prompt the user for input, but stop asking if they fail to provide the information after 2-3 attempts.
- Tools should not be called in a fixed order; determine the sequence based on conversation context.
- If the user mentions a city or tuition fee preference but no `programs` list exists, first call AcademicChainTool to retrieve `programs`, then apply GeneralChainTool.
- Only call GeneralChainTool if `programs` are already available in memory (returned from AcademicChainTool, etc.).
- Ensure that only programs passing all relevant filtering steps remain in the final output.
- Finally, return `program_name`, `university_name`, and generate a recommendation explanation tailored to the user.

Important: You are exclusively focused on recommending English-taught master's programs in Germany. Do not provide information or recommendations about programs in other countries.
"""

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True,
    memory=memory,
    handle_parsing_errors=True,
    agent_kwargs={"system_message": system_prompt}
)


def run_chat():
    print("Welcome to the Master's Program Recommendation Agent. Please provide the necessary information first.")
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        response = agent.run(user_input)
        programs = USER_MEMORY.get("programs", [])
        print("\nAgent:", response)
        print("\nRecommended Programs:", programs)


if __name__=="__main__":
    run_chat()
