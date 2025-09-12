# models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    mobile_number = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # Optional for now
    is_active = Column(Boolean, default=True)
    subscription_tier = Column(String, default="Basic")  # "Basic" or "Pro"
    daily_message_count = Column(Integer, default=0)
    last_message_date = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())

    chatrooms = relationship("Chatroom", back_populates="owner", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")


class Chatroom(Base):
    __tablename__ = "chatrooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=func.now())

    owner = relationship("User", back_populates="chatrooms")
    messages = relationship("Message", back_populates="chatroom", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    is_from_user = Column(Boolean, default=True)  # True = user, False = AI
    chatroom_id = Column(Integer, ForeignKey("chatrooms.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=func.now())

    chatroom = relationship("Chatroom", back_populates="messages")
    user = relationship("User", back_populates="messages")


class SubscriptionEvent(Base):
    __tablename__ = "subscription_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String, nullable=False)  # e.g., "checkout.session.completed"
    stripe_session_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=func.now())

    user = relationship("User")