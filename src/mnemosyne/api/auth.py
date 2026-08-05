import os
import time
import logging
from typing import Optional
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
import bcrypt
from pydantic import BaseModel
from fastapi import Request, HTTPException, status
import logging

logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = os.getenv("MNEMOSYNE_SECRET_KEY", "change_me_in_production_9f8d7e6c5b4a3")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

class Token(BaseModel):
    access_token: str
    token_type: str
    requires_hardware: bool = False

class TokenData(BaseModel):
    username: Optional[str] = None
    hw_bound: bool = False

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        hw_bound = payload.get("hw_bound", False)
        return TokenData(username=username, hw_bound=hw_bound)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Windows Hello / TPM graceful degradation stub
def verify_windows_hello() -> bool:
    """
    Placeholder for Windows Hello / TPM hardware binding.
    In a real implementation, this would use pywin32 or tpm2-pytss.
    For graceful degradation, we return True if running on Windows
    with a specific env var, otherwise False.
    """
    logger.info("Hardware binding check initiated.")
    # Graceful degradation: standard auth fallback if hardware not ready
    return os.getenv("USE_WINDOWS_HELLO", "0") == "1"
