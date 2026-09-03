import os
from dotenv import load_dotenv, find_dotenv
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService,Session
from google.adk.runners import Runner
from google.genai import types
from typing import Optional, Dict, Any

import warnings
warnings.filterwarnings("ignore")
import logging
logging.basicConfig(level=logging.CRITICAL)

print("Libraries imported")

def load_env():
    _ = load_dotenv(find_dotenv())

def get_neo4j_import_dir():
    """Gets the neo4j import directory from an environment variable
    """
    load_env()
    neo4j_import_dir = os.getenv("NEO4J_IMPORT_DIR")
    return neo4j_import_dir


class AgentCaller:
    def __init__(self,agent: Agent,runner: Runner,user_id: str,session_id: str,session_service: InMemorySessionService,
        app_name: Optional[str] = None,
    ):
        """
        初始化 Agent 调用器
        """
        # 如果 app_name 未提供，则使用 agent.name
        self.app_name = app_name if app_name else agent.name
        self.agent = agent
        self.user_id = user_id
        self.session_id = session_id
        self.runner = runner
        # 使用外部传入的同一个 session_service，避免状态不一致
        self.session_service = session_service

        # 内部状态标志，用于确保只创建一次 Session


    async def chat(self, user_input: str, verbose: bool = False) -> str:
        print(f"\n>>>👤 用户: {user_input}")
        if verbose:
            print("\n🤖 Agent 正在思考并执行中...\n")

        message = types.Content(role='user', parts=[types.Part(text=user_input)])
        final_response_text = "智能体没有生成最终响应"

        async for event in self.runner.run_async(
                user_id=self.user_id, session_id=self.session_id, new_message=message
        ):
            if verbose:
                is_final = event.is_final_response()  # 调用方法
                print(
                    f"  [Event] Author: {event.author}, Type: {type(event).__name__}, Final: {is_final}, Content: {event.content}")

            if event.is_final_response():
                # 尝试从 content.parts 中提取文本
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if getattr(part, "text", None):
                            final_response_text = part.text
                            break
                # 如果是升级事件
                elif event.actions and event.actions.escalate:
                    final_response_text = f"Agent escalated: {getattr(event, 'error_message', 'No specific message')}"
                break
        self.session = await self.runner.session_service.get_session(app_name=self.runner.app_name, user_id=self.user_id, session_id=self.session_id)
        print(f"<<< Agent Response: {final_response_text}\n")
        return final_response_text

    def get_session(self):
        return self.runner.session_service.get_session(app_name=self.runner.app_name, user_id=self.user_id, session_id=self.session_id)


async def make_agent_caller(
    agent: Agent,
    app_name: Optional[str] = None,
    initial_state: Optional[Dict[str, Any]] = None,
) -> AgentCaller:
    """
    创建 AgentCaller 实例，准备好 runner 和 session_service。
    """
    # 1. 确定名字
    app_name = app_name or f"{agent.name}_app"
    user_id = f"{agent.name}_user"
    session_id = f"{agent.name}_session"
    session_service = InMemorySessionService()
    # Initialize a session
    await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        state=initial_state
    )
    runner = Runner(
        app_name=app_name,
        agent=agent,
        session_service=session_service,
    )

    # 3. 返回 AgentCaller，由它负责在首次聊天时创建 session
    return AgentCaller(
        agent=agent,
        runner=runner,
        user_id=user_id,
        session_id=session_id,
        session_service=session_service,
        app_name=app_name,
    )