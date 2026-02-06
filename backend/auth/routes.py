from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session
from datetime import datetime
import asyncio

from backend.dependencies import get_db
from backend.auth.service import AuthService
from backend.domain.audit.models import AuditTrail
from backend.domain.common.user import User

router = APIRouter(prefix="/auth", tags=["Auth"])
auth_service = AuthService()

# MVP: Hardcoded User getter for now, usually JWT logic
def get_current_user():
    return User(id="mvp_user", username="trader", full_name="Local Trader")

async def refresh_token_task(db: Session, user_id: str):
    """
    Background task to refresh token before expiry.
    """
    # Logic: Wait until 15 mins before expiry, then refresh
    # For MVP: Just log that monitoring is active
    print(f"[{datetime.now()}] Token Refresh Monitor Active for {user_id}")
    # In real impl: while True: check time -> refresh -> sleep

    # Audit Log
    try:
        audit = AuditTrail(
            user_id=user_id,
            action_type="AUTH_REFRESH_INIT",
            entity_type="SYSTEM",
            entity_id="UPSTOX_SESSION",
            timestamp=datetime.utcnow()
        )
        db.add(audit)
        db.commit()
    except Exception as e:
        print(f"Audit Log Failed: {e}")

@router.get("/login")
def login():
    """Returns the Login URL (Frontend should redirect here)."""
    return {"url": auth_service.get_login_url()}

@router.get("/callback")
def auth_callback(code: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Upstox Redirects here with ?code=...
    """
    try:
        token_data = auth_service.exchange_code_for_token(code)

        # Log Success
        user_id = token_data.get("user_id", "unknown")
        audit = AuditTrail(
            user_id=user_id,
            action_type="LOGIN_SUCCESS",
            entity_type="SYSTEM",
            entity_id="UPSTOX_SESSION",
            after_state={"user_name": token_data.get("user_name")},
            timestamp=datetime.utcnow()
        )
        db.add(audit)
        db.commit()

        # Start Refresh Task
        background_tasks.add_task(refresh_token_task, db, user_id)

        return {"status": "Login Successful", "user": token_data.get("user_name")}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/totp")
def generate_totp_manual(user: User = Depends(get_current_user)):
    """
    For manual 2FA entry if needed.
    """
    return {"totp": auth_service.generate_totp()}
