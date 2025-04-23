# pip install google-adk google-generativeai mcp python-dotenv
import asyncio
import os
import json

# 如果需要，保留日志记录
import logging
from dotenv import load_dotenv
from google.genai import types

# 如果 genai 导入仅用于配置且已被移除，则移除此导入
# import google.generativeai as genai
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

# 从 .env 文件加载环境变量
load_dotenv()

# 启用调试日志记录（如果需要日志记录，请保留此项）
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


# --- 步骤 1: 从 MCP 服务器获取工具 ---
async def get_tools_async():
    """从航班搜索 MCP 服务器获取工具。"""
    print("尝试连接到 MCP 航班搜索服务器...")
    server_params = StdioServerParameters(
        command="mcp-flight-search",
        args=["--connection_type", "stdio"],
        env={"SERP_API_KEY": os.getenv("SERP_API_KEY")},
    )

    tools, exit_stack = await MCPToolset.from_server(connection_params=server_params)
    print("MCP 工具集创建成功。")
    return tools, exit_stack


# --- 步骤 2: 定义 ADK 智能体创建 ---
async def get_agent_async():
    """创建一个配备了来自 MCP 服务器工具的 ADK 智能体。"""
    tools, exit_stack = await get_tools_async()
    print(f"从 MCP 服务器获取了 {len(tools)} 个工具。")

    # 创建与示例结构匹配的 LlmAgent
    root_agent = LlmAgent(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-pro-exp-03-25"),
        name="flight_search_assistant",
        instruction="根据提示使用可用工具帮助用户搜索航班。如果未指定返程日期，则单程旅行使用空字符串。",
        tools=tools,
    )

    return root_agent, exit_stack


# --- 步骤 3: 主要执行逻辑 ---
async def async_main():
    # 创建服务
    session_service = InMemorySessionService()

    # 创建一个会话
    session = session_service.create_session(
        state={}, app_name="flight_search_app", user_id="user_flights"
    )

    # 定义用户提示
    query = "Find flights from Atlanta to Las Vegas 2025-05-05"
    print(f"用户查询: '{query}'")

    # 将输入格式化为 types.Content
    content = types.Content(role="user", parts=[types.Part(text=query)])

    # 获取智能体和 exit_stack
    root_agent, exit_stack = await get_agent_async()

    # 创建 Runner
    runner = Runner(
        app_name="flight_search_app",
        agent=root_agent,
        session_service=session_service,
    )

    print("正在运行智能体...")
    events_async = runner.run_async(
        session_id=session.id, user_id=session.user_id, new_message=content
    )

    async for event in events_async:
        print(f"收到事件: {event}")

    # 始终清理资源
    print("正在关闭 MCP 服务器连接...")
    await exit_stack.aclose()
    print("清理完成。")


# --- 步骤 4: 运行主函数 ---
if __name__ == "__main__":
    # 确保 API 密钥已设置
    if not os.getenv("GOOGLE_API_KEY"):
        raise ValueError("未设置 GOOGLE_API_KEY 环境变量。")
    if not os.getenv("SERP_API_KEY"):
        raise ValueError("未设置 SERP_API_KEY 环境变量。")

    # 运行主异步函数
    asyncio.run(async_main())
