from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from backend.domain.common.user import User

# Mock User DB
USERS_DB = {
    "admin": {"password": "secret_password", "user": User(id="USER-001", username="admin", full_name="Admin User")},
    "trader": {"password": "trade_safe", "user": User(id="USER-002", username="trader", full_name="Trader Joe")}
}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

router = APIRouter(prefix="/auth", tags=["Authentication"])

class Token(BaseModel):
    access_token: str
    token_type: str

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    # Simple Mock: Token is just "username:password" base64 or similar?
    # For demo, let's assume the token IS the username.
    user_entry = USERS_DB.get(token)
    if not user_entry:
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_entry["user"]

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_entry = USERS_DB.get(form_data.username)
    if not user_entry or user_entry["password"] != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Return the username as the "token" for this mock
    return {"access_token": form_data.username, "token_type": "bearer"}
