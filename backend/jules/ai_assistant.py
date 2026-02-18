import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class JulesAssistant:
    def __init__(self):
        self._load_key()

    def _load_key(self):
        # Reload key from file/env
        load_dotenv(override=True)
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None

    async def get_response(self, message: str) -> str:
        # Always reload key before request to catch config changes
        self._load_key()

        if not self.model:
            return "Please configure your Google API Key in Settings to use Jules."

        try:
            chat = self.model.start_chat(history=[])
            response = await chat.send_message_async(message)
            return response.text
        except Exception as e:
            return f"I encountered an error: {str(e)}"

# Singleton instance
jules = JulesAssistant()
