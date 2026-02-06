import pyotp
import os
import requests
from datetime import datetime
from backend.config import Config

class AuthService:
    """
    Handles Upstox Authentication using TOTP.
    """
    def __init__(self):
        self.api_key = Config.MARKET_DATA_KEY
        self.api_secret = Config.UPSTOX_SECRET
        self.totp_secret = os.getenv("UPSTOX_TOTP_SECRET", "JBSWY3DPEHPK3PXP") # Default mock secret
        self.redirect_uri = "http://localhost:8000/auth/callback"
        self.access_token = None
        self.token_expiry = None

    def generate_totp(self) -> str:
        """Generates 6-digit TOTP code."""
        totp = pyotp.TOTP(self.totp_secret)
        return totp.now()

    def get_login_url(self) -> str:
        return f"https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id={self.api_key}&redirect_uri={self.redirect_uri}"

    def exchange_code_for_token(self, auth_code: str) -> dict:
        """
        Exchanges Auth Code for Access Token.
        """
        url = "https://api.upstox.com/v2/login/authorization/token"
        headers = {"accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "code": auth_code,
            "client_id": self.api_key,
            "client_secret": self.api_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code"
        }

        # Mocking for Development/MVP if no real Upstox Creds
        if Config.MODE == "DEVELOPMENT":
            return {
                "access_token": "mock_access_token_xyz",
                "expires_in": 86400,
                "user_id": "mock_user",
                "user_name": "Mock Trader"
            }

        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data.get("access_token")
            # Set expiry (approx)
            self.token_expiry = datetime.now().timestamp() + token_data.get("expires_in", 86400)
            return token_data
        else:
            raise Exception(f"Auth Failed: {response.text}")
