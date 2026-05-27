"""意图识别 — 使用千问大模型分析用户输入，判断需要调用哪些子 Agent"""

import json

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings

INTENT_SYSTEM_PROMPT = """你是一个智能助手路由器，负责分析用户输入并判断需要调用哪些子 Agent。

可用子 Agent 及能力：
1. weather_outfit — 查询天气、气温、穿衣建议、出行推荐（涉及天气、温度、下雨、冷热、穿什么）
2. image_process — 图片生成（画图、生成图片）或图片识别描述（图生文、识别图片里有什么）
3. work_order — 查询个人工单/任务/待办列表（涉及工单、任务、待办事项）

规则：
- 仔细分析用户输入，找出所有匹配的子 Agent
- 如果用户的输入完全不涉及以上任何一个子Agent，tools 返回空数组
- 从用户输入中提取关键参数：城市名、图片URL、生成图片的描述词(prompt)、工单筛选条件(status)等

请严格返回 JSON 格式，不要有其他文字：
{"tools": ["weather_outfit"], "params": {"city": "北京"}, "reply": "正在为你查询北京天气和穿衣建议"}

示例：
- "今天深圳天气怎么样，穿什么" → {"tools": ["weather_outfit"], "params": {"city": "深圳"}, "reply": "正在为你查询深圳天气和出行穿衣建议"}
- "帮我画一幅海边日落的油画" → {"tools": ["image_process"], "params": {"prompt": "海边日落油画", "style": "油画"}, "reply": "正在为你生成海边日落的油画"}
- "我有哪些待处理的工单" → {"tools": ["work_order"], "params": {"status": "待处理"}, "reply": "正在查询你的待处理工单"}
- "北京今天热不热，顺便看看我的工单" → {"tools": ["weather_outfit", "work_order"], "params": {"city": "北京"}, "reply": "正在为你查询北京天气和工单信息"}
- "你好" → {"tools": [], "params": {}, "reply": ""}"""


async def detect_intent(user_input: str) -> dict:
    """使用千问大模型分析用户意图，返回需要调用的工具列表和参数"""
    llm = ChatOpenAI(
        model=settings.QWEN_TEXT_MODEL,
        api_key=settings.QWEN_API_KEY,
        base_url=settings.QWEN_BASE_URL,
        temperature=0,
    )

    response = await llm.ainvoke([
        SystemMessage(content=INTENT_SYSTEM_PROMPT),
        HumanMessage(content=user_input),
    ])

    try:
        result = json.loads(response.content.strip())
        if "tools" not in result:
            result["tools"] = []
        if "params" not in result:
            result["params"] = {}
        if "reply" not in result:
            result["reply"] = ""
        return result
    except json.JSONDecodeError:
        return {"tools": [], "params": {}, "reply": ""}
