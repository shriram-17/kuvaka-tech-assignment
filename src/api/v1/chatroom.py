# src/api/v1/chatroom.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from src.schemas.chatroom import ChatroomCreate, ChatroomResponse, MessageCreate, MessageResponse
from src.models import Chatroom, Message, User
from src.database.session import get_db
from src.core.security import get_current_user
from src.utils.cache import get_cached_chatrooms, cache_chatrooms, invalidate_chatrooms_cache
from src.queue import enqueue_gemini_task  # ✅ RQ integration
import logging

router = APIRouter(prefix="/chatroom", tags=["chatroom"])
logger = logging.getLogger(__name__)

# --- GET /chatroom — CACHED RESPONSE ---
@router.get("", response_model=List[ChatroomResponse])
def list_chatrooms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lists all chatrooms for the authenticated user.
    Uses Redis caching to reduce database load.
    Cache TTL: 5 minutes.
    """
    # Try cache first
    cached = get_cached_chatrooms(str(current_user.id))
    if cached:
        logger.info(f"✅ Serving cached chatrooms for user {current_user.id}")
        return [ChatroomResponse(**c) for c in cached]

    # Fallback to DB
    chatrooms = db.query(Chatroom).filter(Chatroom.user_id == current_user.id).all()

    # Cache result
    chatroom_schemas = [ChatroomResponse.from_orm(c) for c in chatrooms]
    cache_chatrooms(str(current_user.id), [c.model_dump() for c in chatroom_schemas])

    logger.info(f"✅ Cached new chatroom list for user {current_user.id}")
    return chatroom_schemas


# --- POST /chatroom — Create New Chatroom ---
@router.post("", response_model=ChatroomResponse, status_code=status.HTTP_201_CREATED)
def create_chatroom(
    chatroom: ChatroomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Creates a new chatroom for the authenticated user.
    Invalidates cache upon creation.
    """
    new_chat = Chatroom(name=chatroom.name, user_id=current_user.id)
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)

    # ❌ Invalidate cache on creation
    invalidate_chatrooms_cache(str(current_user.id))
    logger.info(f"✅ Created chatroom {new_chat.id} and invalidated cache for user {current_user.id}")

    return new_chat


# --- DELETE /chatroom/{id} ---
@router.delete("/{chatroom_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chatroom(
    chatroom_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deletes a specific chatroom owned by the user.
    Invalidates cache upon deletion.
    """
    chatroom = db.query(Chatroom).filter(
        Chatroom.id == chatroom_id,
        Chatroom.user_id == current_user.id
    ).first()

    if not chatroom:
        raise HTTPException(status_code=404, detail="Chatroom not found")

    db.delete(chatroom)
    db.commit()

    # ❌ Invalidate cache on deletion
    invalidate_chatrooms_cache(str(current_user.id))
    logger.info(f"✅ Deleted chatroom {chatroom_id} and invalidated cache for user {current_user.id}")


# --- GET /chatroom/{id} ---
@router.get("/{chatroom_id}", response_model=ChatroomResponse)
def get_chatroom(
    chatroom_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves detailed information about a specific chatroom.
    Ensures ownership.
    """
    chatroom = db.query(Chatroom).filter(
        Chatroom.id == chatroom_id,
        Chatroom.user_id == current_user.id
    ).first()

    if not chatroom:
        raise HTTPException(status_code=404, detail="Chatroom not found")

    return chatroom


# --- POST /chatroom/{id}/message — ASYNC GEMINI VIA RQ ---
@router.post("/{chatroom_id}/message", response_model=MessageResponse, status_code=status.HTTP_202_ACCEPTED)
def send_message(
    chatroom_id: int,
    message_data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sends a user message and triggers an async Gemini API call via Redis Queue.
    Returns 202 Accepted immediately.
    Implements rate-limiting for Basic tier (5 messages/day).
    """

    # Validate chatroom ownership
    chatroom = db.query(Chatroom).filter(
        Chatroom.id == chatroom_id,
        Chatroom.user_id == current_user.id
    ).first()

    if not chatroom:
        raise HTTPException(status_code=404, detail="Chatroom not found")

    # 🔒 RATE LIMITING: Basic tier = 5 messages/day
    now = datetime.utcnow().date()
    if current_user.subscription_tier == "Basic":
        # Reset counter if date changed
        if current_user.last_message_date.date() < now:
            current_user.daily_message_count = 0
            current_user.last_message_date = now
            db.commit()

        # Enforce limit
        if current_user.daily_message_count >= 5:
            raise HTTPException(
                status_code=429,
                detail="Daily message limit reached (5/day for Basic tier). Upgrade to Pro."
            )

        # Increment count
        current_user.daily_message_count += 1
        db.commit()

    # Save user message
    user_message = Message(
        content=message_data.content,
        is_from_user=True,
        chatroom_id=chatroom_id,
        user_id=current_user.id
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    # ✅ ENQUEUE TASK TO REDIS QUEUE (RQ)
    enqueue_gemini_task(
        message_content=message_data.content,
        chatroom_id=chatroom_id,
        user_id=current_user.id
    )

    logger.info(f"✅ Enqueued Gemini task for message {user_message.id} from user {current_user.id}")

    # Return 202 Accepted immediately
    return user_message


# --- GET /chatroom/{id}/messages ---
@router.get("/{chatroom_id}/messages", response_model=List[MessageResponse])
def get_messages(
    chatroom_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves all messages in a specific chatroom, ordered by time.
    """
    chatroom = db.query(Chatroom).filter(
        Chatroom.id == chatroom_id,
        Chatroom.user_id == current_user.id
    ).first()

    if not chatroom:
        raise HTTPException(status_code=404, detail="Chatroom not found")

    messages = db.query(Message).filter(
        Message.chatroom_id == chatroom_id
    ).order_by(Message.created_at).all()

    return messages