"""千问大模型流式客户端"""

import json
import sys

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


_llm = None
_streaming_llm = None
_intent_llm = None


def build_llm():
    """创建千问大模型实例（非流式）— 模块级复用避免重复建立连接"""
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model=settings.QWEN_TEXT_MODEL,
            api_key=settings.QWEN_API_KEY,
            base_url=settings.QWEN_BASE_URL,
            temperature=0.7,
        )
    return _llm


def build_intent_llm():
    """意图识别专用 LLM（temperature=0 保证确定性输出）"""
    global _intent_llm
    if _intent_llm is None:
        _intent_llm = ChatOpenAI(
            model=settings.QWEN_TEXT_MODEL,
            api_key=settings.QWEN_API_KEY,
            base_url=settings.QWEN_BASE_URL,
            temperature=0,
        )
    return _intent_llm


def build_streaming_llm():
    """创建千问大模型实例（流式）— 模块级复用避免重复建立连接"""
    global _streaming_llm
    if _streaming_llm is None:
        _streaming_llm = ChatOpenAI(
            model=settings.QWEN_TEXT_MODEL,
            api_key=settings.QWEN_API_KEY,
            base_url=settings.QWEN_BASE_URL,
            temperature=0.7,
            streaming=True,
        )
    return _streaming_llm


async def stream_response(user_input: str, tool_results: dict, history: list[dict] | None = None):
    """流式返回：将工具结果合并到上下文，交给大模型流式输出"""
    llm = build_streaming_llm()
    messages = []

    if history:
        for h in history:
            role = h.get("role", "")
            content = h.get("content", "")
            if role == "system":
                messages.append(SystemMessage(content=content))
            elif role == "assistant":
                from langchain_core.messages import AIMessage
                messages.append(AIMessage(content=content))
            elif role == "user":
                messages.append(HumanMessage(content=content))

    if not tool_results:
        messages.append(SystemMessage(content=SUMMARY_PROMPT_NO_TOOLS))
        messages.append(HumanMessage(content=user_input))
    else:
        tools_json = json.dumps(tool_results, ensure_ascii=False, indent=2)
        user_message = f"用户问题：{user_input}\n\n工具返回数据：\n{tools_json}"
        messages.append(SystemMessage(content=SYSTEM_SUMMARY_PROMPT))
        messages.append(HumanMessage(content=user_message))

    count = 0
    try:
        async for chunk in llm.astream(messages):
            if chunk.content:
                count += 1
                yield chunk.content
    except Exception as e:
        print(f"[LLM] stream ERROR after {count} chunks: {e}", file=sys.stderr, flush=True)
        raise
