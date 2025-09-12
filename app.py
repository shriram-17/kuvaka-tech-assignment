# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from models import User, Chatroom, Message, SubscriptionEvent
from schemas import (
    UserCreate, OTPRequest, OTPVerify, Token,
    UserResponse, ChatroomCreate, ChatroomResponse,
    MessageCreate, MessageResponse
)
from auth import generate_otp, store_otp, verify_otp, create_access_token
from database import SessionLocal, engine, Base

# Create tables (run once)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Gemini Backend Clone - Kuvaka Tech")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# === AUTH ENDPOINTS ===

@app.post("/auth/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.mobile_number == user.mobile_number).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Mobile number already registered")
    new_user = User(mobile_number=user.mobile_number)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/auth/send-otp")
def send_otp(request: OTPRequest):
    otp = generate_otp()
    store_otp(request.mobile_number, otp)
    return {
        "message": "OTP generated successfully. (In real app, sent via SMS)",
        "otp": otp  # For assignment purposes only
    }

@app.post("/auth/verify-otp", response_model=Token)
def verify_otp_endpoint(otp_ OTPVerify, db: Session = Depends(get_db)):
    if not verify_otp(otp_data.mobile_number, otp_data.otp):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    user = db.query(User).filter(User.mobile_number == otp_data.mobile_number).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Please signup first.")

    access_token = create_access_token(data={"sub": user.mobile_number})
    return {"access_token": access_token, "token_type": "bearer"}

# === USER ENDPOINT (PROTECTED) ===

@app.get("/user/me", response_model=UserResponse)
def get_current_user_info(db: Session = Depends(get_db)):
    # ⚠️ TEMP: Hardcoded user for demo — In real app, use JWT middleware
    # We'll add JWT auth in next step
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="No user found")
    return user

# === CHATROOM ENDPOINTS (STUBS) ===

@app.post("/chatroom", response_model=ChatroomResponse)
def create_chatroom(chatroom: ChatroomCreate, db: Session = Depends(get_db)):
    # ⚠️ TEMP: Hardcoded user_id=1 — In real app, get from JWT
    new_chat = Chatroom(name=chatroom.name, user_id=1)
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    return new_chat

@app.get("/chatroom", response_model=List[ChatroomResponse])
def list_chatrooms(db: Session = Depends(get_db)):
    # ⚠️ TEMP: Hardcoded user_id=1
    chatrooms = db.query(Chatroom).filter(Chatroom.user_id == 1).all()
    return chatrooms