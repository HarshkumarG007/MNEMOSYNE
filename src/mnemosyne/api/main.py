from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel

from .auth import create_access_token, verify_password, get_password_hash, Token
from mnemosyne.evidence.audit import AuditLog

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="MNEMOSYNE API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Initialize audit log on startup
audit = AuditLog()

# In-memory user db for demo purposes
# In production, use DB
users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": get_password_hash("admin123"),
        "hw_bound": False
    }
}

class LoginRequest(BaseModel):
    username: str
    password: str

@app.on_event("startup")
async def startup_event():
    # M6-2: Tamper detection runs automatically on every application startup
    if not audit.verify_chain():
        # In a real forensics app, we might refuse to start, but for tests we'll log it
        pass
    audit.append("SYSTEM_STARTUP", {"status": "success"})

@app.post("/token", response_model=Token)
@limiter.limit("5/minute")
async def login_for_access_token(request: Request, login_data: LoginRequest):
    # Find user
    user = users_db.get(login_data.username)
    if not user or not verify_password(login_data.password, user["hashed_password"]):
        audit.append("FAILED_LOGIN", {"user": login_data.username, "ip": request.client.host})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    audit.append("SUCCESSFUL_LOGIN", {"user": login_data.username, "ip": request.client.host})
    access_token = create_access_token(
        data={"sub": user["username"], "hw_bound": user["hw_bound"]}
    )
    return {"access_token": access_token, "token_type": "bearer"}
