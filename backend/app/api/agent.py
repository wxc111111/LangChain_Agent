"""Agent API 路由"""

import json
import sys

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator

from app.core.deps import get_current_user
from app.core import memory
from app.database import get_db
from app.agent.intent import detect_intent
from app.agent.dispatcher import dispatch_tools
from app.agent.llm_client import stream_response

router = APIRouter(prefix="/api/agent", tags=["agent"])


def _log(msg: str):
    print(f"[AGENT] {msg}", file=sys.stderr, flush=True)


class ChatRequest(BaseModel):
    message: str = ""
    images: list[str] = []
    conversation_id: int | None = None

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
    db=Depends(get_db),
):
    """Agent 对话入口 — SSE 流式输出"""

    user_input = body.message.strip()
    if not user_input and not body.images:
        return StreamingResponse(
            _single_event({"type": "error", "data": "消息不能为空"}),
            media_type="text/event-stream",
        )

    # 获取或创建会话
    user_id = current_user.id
    conv = memory.get_or_create_conversation(db, user_id, body.conversation_id, user_input)
    conversation_id = conv.id

    async def generate():
        try:
            _log("generate start")
            yield _sse_msg({"type": "meta", "conversation_id": conversation_id})

            # 1. 意图识别
            _log("step1: intent detection")
            intent = await detect_intent(user_input)
            tool_names = intent.get("tools", [])
            reply = intent.get("reply", "")
            params = intent.get("params", {})
            _log(f"step1: done, tools={tool_names}")

            yield _sse_msg({"type": "intent", "tools": tool_names, "reply": reply})

            # 2. 调度子 Agent
            _log("step2: dispatch tools")
            tool_results = await dispatch_tools(tool_names, user_input, params)
            _log(f"step2: done, results_keys={list(tool_results.keys())}")

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

            # 3. 构建上下文（历史记忆）
            _log("step3: build_context")
            history = memory.build_context(user_id, conversation_id, db)
            _log(f"step3: done, history_len={len(history)}")

            # 4. 流式输出大模型总结
            _log("step4: stream_response")
            full_reply = ""
            async for text in stream_response(user_input, tool_results, history):
                full_reply += text
                yield _sse_msg({"type": "content", "data": text})
            _log(f"step4: done, reply_len={len(full_reply)}")

            # 5. 保存本轮对话（失败不影响回复）
            _log("step5: save_turn")
            try:
                memory.save_turn(user_id, conversation_id, user_input or "[图片]", full_reply, db)
                _log("step5: done")
            except Exception as e:
                _log(f"step5: failed - {e}")

            yield _sse_done()
            _log("generate done")

        except Exception as e:
            _log(f"generate ERROR: {e}")
            import traceback
            traceback.print_exc(file=sys.stderr)
            yield _sse_msg({"type": "error", "data": str(e)})
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
