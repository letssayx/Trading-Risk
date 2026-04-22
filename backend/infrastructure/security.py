from typing import Optional

class SecurityManager:
    """
    Manages Security & Authentication (TOTP, Session, RBAC).
    Currently a mock implementation for the Institutional Shell.
    """

    def __init__(self):
        self.active_sessions = {}

    def generate_totp_secret(self, user_id: str) -> str:
        """
        Generates a new TOTP secret for the user (Mock).
        In production, use pyotp.random_base32().
        """
        return f"MOCK_SECRET_{user_id}_123"

    def verify_totp(self, user_id: str, token: str) -> bool:
        """
        Verifies a TOTP token.
        Mock: Any 6-digit token is valid for now.
        """
        return len(token) == 6 and token.isdigit()

    def create_session(self, user_id: str) -> str:
        """
        Creates a session token.
        """
        import uuid
        token = str(uuid.uuid4())
        self.active_sessions[token] = user_id
        return token

    def validate_session(self, token: str) -> Optional[str]:
        return self.active_sessions.get(token)
