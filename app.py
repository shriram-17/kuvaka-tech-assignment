# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.models import User, Chatroom
from src.schema import (
    UserCreate, OTPRequest, OTPVerify, Token,
    UserResponse, ChatroomCreate, ChatroomResponse
)
from src.auth import (
    generate_otp, store_otp, verify_otp, create_access_token,
    get_current_user # <-- Import the JWT middleware dependency
)
from src.database import SessionLocal, engine, Base

# Create tables (run once)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Gemini Backend Clone - Kuvaka Tech")

# Dependency for DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# === AUTH ENDPOINTS (UNCHANGED) ===

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
def verify_otp_endpoint(otp_data: OTPVerify, db: Session = Depends(get_db)):
    if not verify_otp(otp_data.mobile_number, otp_data.otp):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    user = db.query(User).filter(User.mobile_number == otp_data.mobile_number).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Please signup first.")

    access_token = create_access_token(data={"sub": user.mobile_number})
    return {"access_token": access_token, "token_type": "bearer"}

# === PROTECTED ENDPOINTS (UPDATED) ===

@app.get("/user/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Protected endpoint. Returns details of the currently authenticated user.
    """
    return current_user

@app.post("/chatroom", response_model=ChatroomResponse)
def create_chatroom(
    chatroom: ChatroomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # <-- Middleware protects this endpoint
):
    """
    Creates a new chatroom for the authenticated user.
    Uses the 'current_user' object provided by the JWT middleware.
    """
    new_chat = Chatroom(name=chatroom.name, user_id=current_user.id)
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    return new_chat

@app.get("/chatroom", response_model=List[ChatroomResponse])
def list_chatrooms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # <-- Middleware protects this endpoint
):
    """
    Lists all chatrooms for the authenticated user.
    Uses the 'current_user' object to filter results.
    """
    chatrooms = db.query(Chatroom).filter(Chatroom.user_id == current_user.id).all()
    return chatrooms

@app.get("/chatroom/{chatroom_id}", response_model=ChatroomResponse)
def get_chatroom(
    chatroom_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves a specific chatroom by ID, ensuring it belongs to the authenticated user.
    """
    chatroom = db.query(Chatroom).filter(
        Chatroom.id == chatroom_id,
        Chatroom.user_id == current_user.id # Security: Ensure user owns the chatroom
    ).first()

    if not chatroom:
        raise HTTPException(status_code=404, detail="Chatroom not found")

    return chatroom