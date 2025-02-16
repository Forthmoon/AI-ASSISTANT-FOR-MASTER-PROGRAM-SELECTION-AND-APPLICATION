import os
from flask import Blueprint, request, jsonify
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_models import ChatOpenAI
from typing import Dict, Any
import json

chatbot_bp = Blueprint('chatbot', __name__)


class ChatbotAgent:
    def __init__(self, db_queries: Any, llm_config: Dict[str, Any]):
        self.llm = ChatOpenAI(
            temperature=llm_config["temperature"],
            model_name=llm_config["model_name"],
            openai_api_key=llm_config["api_key"]
        )
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.db = db_queries
        self.agent = initialize_agent(
            self._create_tools(),
            self.llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True
        )

    def _create_tools(self):
        return [
            {
                "name": "AcademicFilter",
                "func": self._wrap_chain("academic"),
                "description": "Filter programs by academic background and major"
            },
            {
                "name": "LanguageFilter",
                "func": self._wrap_chain("language"),
                "description": "Filter by language requirements (IELTS/TOEFL)"
            },
            {
                "name": "GMAT_GRE_Filter",
                "func": self._wrap_chain("gmat_gre"),
                "description": "Filter by GMAT/GRE requirements considering nationality"
            },
            {
                "name": "GeneralFilter",
                "func": self._wrap_chain("general"),
                "description": "Filter by city, tuition and duration preferences"
            },
            {
                "name": "RankingFilter",
                "func": self._wrap_chain("ranking"),
                "description": "Filter by QS university and subject rankings"
            }
        ]

    def _wrap_chain(self, chain_type):
        def wrapper(input_str: str):
            parsed_params = self._parse_input(input_str)
            return getattr(self, f"_execute_{chain_type}_chain")(parsed_params)

        return wrapper

    def _parse_input(self, input_str: str) -> Dict[str, Any]:
        prompt = f"""Extract parameters from:
        {input_str}
        Return JSON with: bachelor_major, preferred_subject, ielts_score, 
        toefl_score, gmat_score, gre_score, country, city_preference, 
        tuition_preference, duration_preference, qs_ranking"""

        response = self.llm.invoke(prompt)
        return json.loads(response.content)

    def _execute_academic_chain(self, params):
        # 调用原有academic_chain逻辑
        from app_final.recommendation.chains.academic_chain import filter_programs_by_subject_and_major
        return filter_programs_by_subject_and_major(
            params.get("preferred_subject"),
            params.get("bachelor_major"),
            self.llm
        )

    # 其他链的包装方法类似...

    def process_message(self, user_id: str, message: str):
        try:
            response = self.agent.run(message)
            return {
                "results": response.get("programs", []),
                "explanation": response.get("explanation", ""),
                "conversation_id": user_id
            }
        except Exception as e:
            return {"error": str(e)}

# 初始化（在recommendation.py中连接）
if __name__ == "__main__":
    import sys
    from pathlib import Path

    # 设置项目根目录
    project_root = Path(__file__).parent.parent.parent
    sys.path.append(str(project_root))


    # 模拟数据库查询模块
    class DBCaller:
        @staticmethod
        def fetch_programs_by_subject_ids(subject_ids):
            # 实际调用你的 db_queries 函数
            from app_final.db import db_queries
            return db_queries.fetch_programs_by_subject_ids(subject_ids)

        # 为其他函数添加类似包装...


    # 配置参数
    llm_config = {
        "temperature": 0.7,
        "model_name": "gpt-3.5-turbo",
        "api_key": os.getenv("OPENAI_API_KEY")  # 确保已设置环境变量
    }

    # 初始化聊天机器人
    bot = ChatbotAgent(db_queries=DBCaller(), llm_config=llm_config)

    # 交互式测试
    print("=== 德国硕士推荐系统测试模式 ===")
    print("输入你的需求（例如：计算机科学 雅思6.5），输入 exit 退出")

    while True:
        try:
            user_input = input("\n> ")
            if user_input.lower() in ["exit", "quit"]:
                break

            response = bot.process_message("test_user", user_input)

            if "error" in response:
                print(f"错误: {response['error']}")
                continue

            print("\n推荐结果：")
            for idx, program in enumerate(response["results"], 1):
                print(f"{idx}. {program[1]} - {program[3]}")
                print(f"   理由: {response.get('explanation', '暂无说明')}")
                print("-" * 60)

        except KeyboardInterrupt:
            print("\n测试终止")
            break



