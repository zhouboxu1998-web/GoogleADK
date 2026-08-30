import os
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from typing import Optional,Dict,Any

import warnings
warnings.filterwarnings("ignore")

import logging
logging.basicConfig(level=logging.CRITICAL)

print("Libraries imported")



class AgentCaller:
    def __init__(self, agent: Agent, runner: Runner, user_id: str, session_id: str, verbose: bool = False):
        """
        初始化 Agent 调用器
        """
        self.verbose = verbose
        self.agent = agent
        # 如果不传参数，就自动根据 agent 的名字生成默认 ID
        self.app_name = app_name
        self.user_id = user_id
        self.session_id = session_id
        self.runner = runner

        # 实例化基础服务
        self.session_service = InMemorySessionService()

        # 内部状态标志，用于确保只创建一次 Session
        self._session_created = False

    async def chat(self, user_input: str) -> str:
        """
        发送消息并获取 Agent 的回复
        """
        # 1. 确保在第一次聊天时创建好 Session
        if not self._session_created:
            await self.session_service.create_session(
                app_name=self.app_name,
                user_id=self.user_id,
                session_id=self.session_id
            )
            self._session_created = True

        print(f"\n>>>👤 用户: {user_input}")
        if self.verbose:
            print("\n🤖 Agent 正在思考并执行中...\n")

        # 2. 组装输入消息
        message = types.Content(role='user', parts=[types.Part(text=user_input)])
        final_response_text = "智能体没有生成最终响应"

        # 3. 异步运行 Agent，抓取事件流
        async for event in self.runner.run_async(user_id=self.user_id, session_id=self.session_id, new_message=message):

            # 调试模式打印所有事件详情
            if self.verbose:
                is_final = getattr(event, "is_final_response", False)
                print(f"  [Event] Author: {getattr(event, 'author', 'N/A')}, Type: {type(event).__name__}, Final: {is_final}, Content: {getattr(event, 'content', 'N/A')}")

            # 4. 提取最终的回复内容
            if getattr(event, "is_final_response", False):
                if getattr(event, "content", None) and event.content.parts:
                    final_response_text = event.content.parts[0].text
                elif getattr(event, "actions", None) and getattr(event.actions, "escalate", None):
                    final_response_text = f"Agent escalated: {getattr(event, 'error_message', 'No specific message')}"

                # 抓到最终回复后，直接跳出循环
                break

        print(f"<<< Agent Response: {final_response_text}\n")
        return final_response_text

async def make_agent_caller(agent: Agent,                                  # 指定必须传一个 Agent 对象
    app_name: Optional[str] = None,
    initial_state: Optional[Dict[str, Any]] = None) -> AgentCaller:
    # 1. 搞定名字
    app_name = app_name or f"{agent.name}_app"
    user_id = f"{agent.name}_user"
    session_id = f"{agent.name}_session"

    # 2. 搞定异步的会话创建（把需要 await 的脏活累活全在这里做完）
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        state=initial_state
    )

    # 3. 组装 Runner
    runner = Runner(
        app_name=app_name,
        agent=agent,
        session_service=session_service
    )

    # 4. 关键：把准备好的东西塞进对象里，并返回这个完美的对象！
    return AgentCaller(agent=agent, runner=runner, user_id=user_id, session_id=session_id)