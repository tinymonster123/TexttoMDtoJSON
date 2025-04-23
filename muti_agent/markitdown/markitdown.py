# pip install google-adk google-generativeai mcp python-dotenv
import os

# 如果需要，保留日志记录
import logging
from dotenv import load_dotenv

# 如果 genai 导入仅用于配置且已被移除，则移除此导入
# import google.generativeai as genai
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

# 从 .env 文件加载环境变量
load_dotenv()

# 启用调试日志记录（如果需要日志记录，请保留此项）
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


# --- 步骤 1: 从 MCP 服务器获取工具 ---
async def get_tools_async():
    """从 markitdown MCP 服务器获取工具。"""
    print("尝试连接到 MCP 航班搜索服务器...")
    server_params = StdioServerParameters(
        command="markitdown-mcp",
        # args=["--connection_type", "stdio"],
        # env={"SERP_API_KEY": os.getenv("SERP_API_KEY")},
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
    text_to_markdown_agent = LlmAgent(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-pro-exp-03-25"),
        name="MarkdownMage",
        instruction="""
        You are MarkdownMage, a Markdown transformation assistant.
        Transform any user‑provided plain text into clear, well‑structured, and idiomatic Markdown.
        Use appropriate headings, lists, links, code blocks, and other Markdown elements.
        Ensure the output is concise, readable, and follows best practices for Markdown syntax.
        """,
        description="将用户输入的文本转换为结构化且美观的 Markdown 格式。",
        tools=tools,
    )

    return text_to_markdown_agent, exit_stack


# --- 步骤 3: 主要执行逻辑 ---
# async def async_main():
#     # 创建服务
#     session_service = InMemorySessionService()

#     # 创建一个会话
#     session = session_service.create_session(
#         state={}, app_name="markitdown_app", user_id="user_flights"
#     )

#     # 定义用户提示
#     query = "Find flights from Atlanta to Las Vegas 2025-05-05"
#     print(f"用户查询: '{query}'")

#     # 将输入格式化为 types.Content
#     content = types.Content(role="user", parts=[types.Part(text=query)])

#     # 获取智能体和 exit_stack
#     root_agent, exit_stack = await get_agent_async()

#     # 创建 Runner
#     runner = Runner(
#         app_name="markitdown_app",
#         agent=root_agent,
#         session_service=session_service,
#     )

#     print("正在运行智能体...")
#     events_async = runner.run_async(
#         session_id=session.id, user_id=session.user_id, new_message=content
#     )

#     async for event in events_async:
#         print(f"收到事件: {event}")

#     # 始终清理资源
#     print("正在关闭 MCP 服务器连接...")
#     try:
#         await exit_stack.aclose()
#     except Exception as e:
#         logging.error(f"关闭 MCP 服务器时出错: {e}")
#     print("清理完成。")
