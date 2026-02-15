from datetime import datetime
import json
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import uuid
from backend.dependencies import engine, SessionLocal

# 1. Define Model
Base = declarative_base()

class AuditLog(Base):
    __tablename__ = 'audit_logs'

    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user = Column(String)
    action = Column(String)
    resource = Column(String)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    # changes = Column(JSON, nullable=True) # Complexity: Request body consumption

# 2. Ensure Table Exists
Base.metadata.create_all(bind=engine)

# 3. Define Middleware
class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Capture Start Time
        start_time = datetime.utcnow()

        # Identify User (Mock or extract from state/header)
        # Assuming Auth middleware runs before this and sets request.state.user
        user_id = "anonymous"
        if hasattr(request.state, "user"):
             user_id = getattr(request.state.user, "id", "anonymous")

        # Process Request
        try:
            response = await call_next(request)
        except Exception as exc:
            # Could log exception here too
            raise exc

        # Log After Response (simplified, synchronous blocking write for now)
        # In prod, push to a queue (Celery/Redis)
        try:
            entry = AuditLog(
                id=str(uuid.uuid4()),
                timestamp=start_time,
                user=user_id,
                action=request.method,
                resource=request.url.path,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get('user-agent')
            )

            # Write to DB
            db = SessionLocal()
            db.add(entry)
            db.commit()
            db.close()

        except Exception as e:
            print(f"Audit Log Failed: {e}")

        return response
