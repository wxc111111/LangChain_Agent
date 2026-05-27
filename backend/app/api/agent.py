"""Agent API 路由"""

import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator

from app.core.deps import get_current_user
from app.agent.intent import detect_intent
from app.agent.dispatcher import dispatch_tools
from app.agent.llm_client import stream_response

router = APIRouter(prefix="/api/agent", tags=["agent"])


class ChatRequest(BaseModel):
    message: str = ""
    images: list[str] = []

    @field_validator("images")
    @classmethod
    def max_three_images(cls, v):
        if len(v) > 3:
            raise ValueError("最多上传3张图片")
        return v


@router.post("/chat")
async def chat(
    body: ChatRequest,
    current_user=Depends(get_current_user),
):
    """Agent 对话入口 — SSE 流式输出"""

    user_input = body.message.strip()
    if not user_input and not body.images:
        return StreamingResponse(
            _single_event({"type": "error", "data": "消息不能为空"}),
            media_type="text/event-stream",
        )

    async def generate():
        # 1. 意图识别
        intent = await detect_intent(user_input)
        tool_names = intent.get("tools", [])
        reply = intent.get("reply", "")
        params = intent.get("params", {})

        yield _sse_msg({"type": "intent", "tools": tool_names, "reply": reply})

        # 2. 调度子 Agent
        tool_results = await dispatch_tools(tool_names, user_input, params)

        # 2.5 处理上传图片 — 逐张调用图生文
        if body.images:
            from app.agent.tools.image_process import ImageToTextTool

            img_descriptions = []
            for img_url in body.images:
                try:
                    desc = await ImageToTextTool.describe(img_url)
                    img_descriptions.append(desc)
                except Exception as e:
                    img_descriptions.append({"image_url": img_url, "error": str(e)})
            tool_results["image_descriptions"] = img_descriptions

        if tool_results:
            yield _sse_msg({"type": "tool_results", "data": tool_results})

        # 3. 流式输出大模型总结
        async for text in stream_response(user_input, tool_results):
            yield _sse_msg({"type": "content", "data": text})

        yield _sse_done()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _sse_msg(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _sse_done() -> str:
    return "data: [DONE]\n\n"


async def _single_event(data: dict):
    yield _sse_msg(data)
    yield _sse_done()
