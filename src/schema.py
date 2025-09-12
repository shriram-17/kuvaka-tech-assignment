# schemas.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

# === AUTH ===
class UserCreate(BaseModel):
    mobile_number: str = Field(..., min_length=10, max_length=15)

class OTPRequest(BaseModel):
    mobile_number: str = Field(..., min_length=10, max_length=15)

class OTPVerify(BaseModel):
    mobile_number: str = Field(..., min_length=10, max_length=15)
    otp: str = Field(..., min_length=4, max_length=6)

class Token(BaseModel):
    access_token: str
    token_type: str

# === USER ===
class UserResponse(BaseModel):
    id: int
    mobile_number: str
    subscription_tier: str
    daily_message_count: int
    last_message_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True  # Important for ORM

# === CHATROOM ===
class ChatroomCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class ChatroomResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True

# === MESSAGE ===
class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1)

class MessageResponse(BaseModel):
    id: int
    content: str
    is_from_user: bool
    created_at: datetime

    class Config:
        from_attributes = True