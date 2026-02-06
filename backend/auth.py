import requests
import webbrowser
import os
from backend.config import Config

class TurtleAuth:
    @staticmethod
    def get_login_url():
        """Step 1: Generates the URL where you manually login to Upstox."""
        client_id = Config.MARKET_DATA_KEY  # Your API Key (Client ID)
        redirect_uri = "http://127.0.0.1:5000"
        url = f"https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}"
        print(f"🐢 Turtle is opening your browser for NSE login...")
        # Check if running in headless env to avoid crash
        try:
            webbrowser.open(url)
        except Exception:
            print(f"   Please open this URL manually: {url}")
        return url

    @staticmethod
    def exchange_code_for_token(auth_code):
        """Step 2: Swaps the temporary code for a 24-hour Access Token."""
        url = 'https://api.upstox.com/v2/login/authorization/token'

        client_secret = os.getenv("UPSTOX_API_SECRET")
        if not client_secret:
            print("❌ UPSTOX_API_SECRET is missing from environment.")
            return None

        data = {
            'code': auth_code,
            'client_id': Config.MARKET_DATA_KEY,
            'client_secret': client_secret,
            'redirect_uri': "http://127.0.0.1:5000",
            'grant_type': 'authorization_code'
        }
        headers = {'accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'}

        try:
            response = requests.post(url, headers=headers, data=data)
            if response.status_code == 200:
                token = response.json().get('access_token')
                print("✅ Access Token Secured. Turtle Terminal is now LIVE.")
                return token
            else:
                print(f"❌ Auth Failed: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Request Error: {e}")
            return None
