from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.conversation import Conversation, Message, MessageRole
import redis
from app.config import settings

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


def _clear_redis(user_id: int, conv_id: int):
    try:
        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
        )
        r.delete(f"chat:{user_id}:{conv_id}")
    except Exception:
        pass


@router.get("")
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    convs = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id, Conversation.is_active == True)
        .order_by(desc(Conversation.updated_at))
        .all()
    )
    return [
        {
            "id": c.id,
            "title": c.title,
            "round_count": c.round_count,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
        for c in convs
    ]


@router.get("/{conv_id}/messages")
def get_messages(
    conv_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conv_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")

    msgs = (
        db.query(Message)
        .filter(Message.conversation_id == conv_id)
        .order_by(Message.created_at)
        .all()
    )
    return [
        {"role": m.role.value, "content": m.content, "created_at": m.created_at.isoformat()}
        for m in msgs
    ]


@router.delete("/{conv_id}")
def remove_conversation(
    conv_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conv_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")

    conv.is_active = False
    db.commit()
    _clear_redis(current_user.id, conv_id)
    return {"ok": True}
