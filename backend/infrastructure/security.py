from typing import Dict, Optional
import pyotp
import uuid

class SecurityManager:
    """
    Manages Security & Authentication (TOTP, Session, RBAC).
    Real implementation using PyOTP.
    """

    def __init__(self):
        self.active_sessions: Dict[str, str] = {} # token -> user_id
        # In-memory storage for secrets (since we don't have a User DB yet)
        self.user_secrets: Dict[str, str] = {} # user_id -> secret

    def generate_totp_secret(self, user_id: str) -> str:
        """
        Generates a new TOTP secret for the user.
        """
        secret = pyotp.random_base32()
        self.user_secrets[user_id] = secret
        return secret

    def verify_totp(self, user_id: str, token: str) -> bool:
        """
        Verifies a TOTP token using the stored secret.
        """
        secret = self.user_secrets.get(user_id)
        if not secret:
            # If no secret exists for user, we can't verify.
            # For dev/testing, maybe we allow a specific fallback or fail.
            # Failing is safer for "Real" mode.
            return False

        totp = pyotp.TOTP(secret)
        return totp.verify(token)

    def create_session(self, user_id: str) -> str:
        """
        Creates a session token.
        """
        token = str(uuid.uuid4())
        self.active_sessions[token] = user_id
        return token

    def validate_session(self, token: str) -> Optional[str]:
        return self.active_sessions.get(token)
