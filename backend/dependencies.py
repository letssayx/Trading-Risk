import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

# Database Setup
# Using a default for development/testing if env not set
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from fastapi import Header, HTTPException, status

def get_current_user():
    # Mock user for now as Auth middleware might be missing or complex
    return {"id": "user_123", "username": "trader"}

def require_admin(x_admin_token: str = Header(None, alias="X-Admin-Token")):
    expected_token = os.getenv("ADMIN_TOKEN")
    if not expected_token:
        # If no ADMIN_TOKEN is set in the environment, fallback to a secure behavior
        # Could be failing all requests or using a dev default. Let's fail secure.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: ADMIN_TOKEN not set."
        )
    if not x_admin_token or x_admin_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing admin token."
        )
    return True
