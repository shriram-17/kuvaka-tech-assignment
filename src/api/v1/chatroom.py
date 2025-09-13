# src/api/v1/chatroom.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from src.schemas.chatroom import ChatroomCreate, ChatroomResponse, MessageCreate, MessageResponse
from src.models import Chatroom, Message, User
from src.database.session import get_db
from src.core.security import get_current_user

router = APIRouter(prefix="/chatroom", tags=["chatroom"])

@router.post("", response_model=ChatroomResponse)
def create_chatroom(
    chatroom: ChatroomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_chat = Chatroom(name=chatroom.name, user_id=current_user.id)
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    return new_chat

@router.get("", response_model=List[ChatroomResponse])
def list_chatrooms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    chatrooms = db.query(Chatroom).filter(Chatroom.user_id == current_user.id).all()
    return chatrooms

@router.get("/{chatroom_id}", response_model=ChatroomResponse)
def get_chatroom(
    chatroom_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    chatroom = db.query(Chatroom).filter(
        Chatroom.id == chatroom_id,
        Chatroom.user_id == current_user.id
    ).first()

    if not chatroom:
        raise HTTPException(status_code=404, detail="Chatroom not found")

    return chatroom