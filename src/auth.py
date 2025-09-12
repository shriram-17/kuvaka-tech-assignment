# auth.py
import secrets
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import User
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ⚠️ In-memory OTP store — Use Redis in production
otp_store: Dict[str, Dict[str, Any]] = {}

# Define the OAuth2 scheme for JWT
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/verify-otp")

def generate_otp() -> str:
    return f"{secrets.randbelow(1000000):06}"

def store_otp(mobile_number: str, otp: str):
    otp_store[mobile_number] = {
        "otp": otp,
        "created_at": datetime.utcnow()
    }

def verify_otp(mobile_number: str, otp: str) -> bool:
    record = otp_store.get(mobile_number)
    if not record:
        return False
    if record["otp"] != otp:
        return False
    if datetime.utcnow() > record["created_at"] + timedelta(minutes=10):
        del otp_store[mobile_number]
        return False
    del otp_store[mobile_number]
    return True

def create_access_token(data:dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Dependency to get the current authenticated user from the JWT token.
    Raises an HTTPException if the token is invalid or the user doesn't exist.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Extract the mobile_number (which we stored as 'sub')
        mobile_number: str = payload.get("sub")
        if mobile_number is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Fetch the user from the database
    user = db.query(User).filter(User.mobile_number == mobile_number).first()
    if user is None:
        raise credentials_exception

    return user