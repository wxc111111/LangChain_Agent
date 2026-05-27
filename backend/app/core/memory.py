import json
import asyncio
import sys

import redis
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models.conversation import Conversation, Message, MessageRole

_redis = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    decode_responses=True,
)

SUMMARY_THRESHOLD = 10   # 轮次阈值
KEEP_RECENT = 5          # 摘要后保留最近 N 轮
REDIS_TTL = 1800         # 30 分钟

SUMMARY_PROMPT = """请用1-2句话总结以下对话的关键信息，包括用户问过什么、助手已经做了什么。
已有摘要：{old_summary}
新对话：
{recent_text}"""


def _redis_key(user_id: int, conv_id: int) -> str:
    return f"chat:{user_id}:{conv_id}"


def get_or_create_conversation(db: Session, user_id: int, conv_id: int | None, first_message: str) -> Conversation:
    if conv_id:
        conv = db.query(Conversation).filter(
            Conversation.id == conv_id,
            Conversation.user_id == user_id,
        ).first()
        if conv:
            return conv

    title = first_message[:50].replace("\n", " ") if first_message else "新对话"
    conv = Conversation(user_id=user_id, title=title)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def build_context(user_id: int, conv_id: int, db: Session | None = None) -> list[dict]:
    """构建给 LLM 的消息上下文：摘要 + 最近 N 轮"""
    messages = []

    # 读 MySQL 摘要
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    try:
        conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
        summary = conv.summary if conv else None
    finally:
        if close_db:
            db.close()

    if summary:
        messages.append({"role": "system", "content": f"[对话历史摘要]: {summary}"})

    # 读 Redis 最近消息（Redis 不可用时静默跳过）
    try:
        key = _redis_key(user_id, conv_id)
        raw = _redis.lrange(key, 0, -1)
        for item in raw:
            try:
                msg = json.loads(item)
                messages.append(msg)
            except json.JSONDecodeError:
                pass
    except Exception as e:
        print(f"[MEMORY] build_context redis error: {e}", file=sys.stderr, flush=True)

    return messages


def save_turn(user_id: int, conv_id: int, user_msg: str, assistant_msg: str, db: Session | None = None):
    """保存一轮对话到 Redis（短期）和 MySQL（长期）"""
    key = _redis_key(user_id, conv_id)

    # 写 Redis（不可用时静默跳过，不阻塞对话）
    try:
        _redis.rpush(key, json.dumps({"role": "user", "content": user_msg}, ensure_ascii=False))
        _redis.rpush(key, json.dumps({"role": "assistant", "content": assistant_msg}, ensure_ascii=False))
        _redis.expire(key, REDIS_TTL)
    except Exception as e:
        print(f"[MEMORY] save_turn redis error: {e}", file=sys.stderr, flush=True)

    # 写 MySQL
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    try:
        db.add(Message(conversation_id=conv_id, role=MessageRole.user, content=user_msg))
        db.add(Message(conversation_id=conv_id, role=MessageRole.assistant, content=assistant_msg))
        conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
        if conv:
            conv.round_count = (conv.round_count or 0) + 1
            if not conv.title or conv.title == "新对话":
                conv.title = user_msg[:50].replace("\n", " ")
        db.commit()
    finally:
        if close_db:
            db.close()

    # 摘要检查移到 build_context 入口，不在这里创建后台任务


async def _maybe_summarize(user_id: int, conv_id: int):
    """超过阈值时异步生成摘要"""
    try:
        key = _redis_key(user_id, conv_id)
        count = _redis.llen(key)
        threshold_msgs = SUMMARY_THRESHOLD * 2  # user + assistant 各一条

        if count <= threshold_msgs:
            return

        # 取最旧 10 条消息（5 轮）
        old_raw = _redis.lrange(key, 0, threshold_msgs - 1)
        old_messages = []
        for item in old_raw:
            try:
                m = json.loads(item)
                old_messages.append(f"{'用户' if m['role']=='user' else '助手'}: {m['content']}")
            except json.JSONDecodeError:
                pass
        recent_text = "\n".join(old_messages)

        # 读已有摘要
        db = SessionLocal()
        old_summary = ""
        try:
            conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
            if conv:
                old_summary = conv.summary or ""
        finally:
            db.close()

        # 调用大模型生成摘要
        prompt = SUMMARY_PROMPT.format(old_summary=old_summary or "无", recent_text=recent_text)
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage
            llm = ChatOpenAI(
                model=settings.QWEN_TEXT_MODEL,
                api_key=settings.QWEN_API_KEY,
                base_url=settings.QWEN_BASE_URL,
                temperature=0.3,
            )
            resp = await llm.ainvoke([HumanMessage(content=prompt)])
            new_summary = resp.content.strip()
        except Exception:
            return

        # 写 MySQL
        db = SessionLocal()
        try:
            conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
            if conv:
                conv.summary = new_summary
                db.commit()
        finally:
            db.close()

        # Redis 只保留最近 5 轮
        _redis.ltrim(key, - (KEEP_RECENT * 2), -1)
        _redis.expire(key, REDIS_TTL)
    except Exception:
        pass


def delete_conversation(user_id: int, conv_id: int):
    """删除会话（MySQL 级联删除消息，Redis 清理）"""
    try:
        _redis.delete(_redis_key(user_id, conv_id))
    except Exception:
        pass
    db = SessionLocal()
    try:
        db.query(Conversation).filter(
            Conversation.id == conv_id,
            Conversation.user_id == user_id,
        ).delete()
        db.commit()
    finally:
        db.close()
