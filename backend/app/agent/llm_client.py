"""千问大模型流式客户端"""

import json
from app.config import settings
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

SYSTEM_SUMMARY_PROMPT = """你是一个专业的智能助手，擅长根据数据回答用户问题。

回答规则：
1. 严格根据工具返回的数据回答，逐条核对数据中的数字（如total、数量），禁止编造
2. 回答简洁清晰、条理分明，直接给结果
3. 如果工具返回了天气数据，先说明温度、天气、湿度、风力，再给出穿衣建议
4. 如果工单数据中total > 0，必须逐条列出工单，按状态分组；只有当total确实为0时才说"没有工单"
5. 如果工具返回了图片描述，用自然语言转述图片内容
6. 如果工具返回了生成的图片链接，把图片URL原样展示给用户
7. 如果工具执行出错，告知用户错误原因并建议重试
8. 用中文回答
9. 回答完直接结束，不要追加"需要我帮你"、"随时告诉我"等客套话"""

SUMMARY_PROMPT_NO_TOOLS = """你是一个友好的智能助手。用户的问题不需要调用工具，请直接、简洁地回答用户。

如果用户只是打招呼（你好、hi），简短友好地回应。
如果用户问你的能力，告诉他你可以：查询天气及穿衣推荐、生成/识别图片、查询工单任务。
用中文回答。"""


def build_llm():
    """创建千问大模型实例（非流式）"""
    return ChatOpenAI(
        model=settings.QWEN_TEXT_MODEL,
        api_key=settings.QWEN_API_KEY,
        base_url=settings.QWEN_BASE_URL,
        temperature=0.7,
    )


def build_streaming_llm():
    """创建千问大模型实例（流式）"""
    return ChatOpenAI(
        model=settings.QWEN_TEXT_MODEL,
        api_key=settings.QWEN_API_KEY,
        base_url=settings.QWEN_BASE_URL,
        temperature=0.7,
        streaming=True,
    )


async def stream_response(user_input: str, tool_results: dict):
    """流式返回：将工具结果合并到上下文，交给大模型流式输出"""
    llm = build_streaming_llm()

    if not tool_results:
        messages = [
            SystemMessage(content=SUMMARY_PROMPT_NO_TOOLS),
            HumanMessage(content=user_input),
        ]
    else:
        tools_json = json.dumps(tool_results, ensure_ascii=False, indent=2)
        user_message = f"用户问题：{user_input}\n\n工具返回数据：\n{tools_json}"
        messages = [
            SystemMessage(content=SYSTEM_SUMMARY_PROMPT),
            HumanMessage(content=user_message),
        ]

    async for chunk in llm.astream(messages):
        if chunk.content:
            yield chunk.content
