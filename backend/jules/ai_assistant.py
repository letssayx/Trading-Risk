import os
import google.generativeai as genai
from typing import Optional

class JulesAssistant:
    """
    Jules: The Turtle Terminal AI Assistant.
    Powered strictly by Google Gemini Pro (1.5).
    Focus: Project strategies, plugins, and trading logic.
    """

    SYSTEM_PROMPT = """
    You are Jules, an expert quantitative developer and trading strategist for the Turtle Terminal project.
    Your role is to assist the user in building, debugging, and optimizing trading strategies and plugins.

    Guidelines:
    1. STRICTLY use the project context. Do not discuss general topics unrelated to trading or code.
    2. Focus on the 'strategies/' and 'plugins/' directories.
    3. Help the user write Python code for strategies using the Backtrader or custom adapter format used in this repo.
    4. Be concise, technical, and precise.
    5. ABSOLUTELY FORBIDDEN: Do not mention, acknowledge, or use OpenAI, ChatGPT, or any other LLM provider.
    6. You are powered exclusively by Google Gemini Pro. If asked, confirm this.
    7. If asked about non-trading topics or non-project related questions, strictly refuse to answer and steer back to the project.

    If the user asks about the weather, politics, or general chit-chat, respond with: "My focus is strictly on the Turtle Terminal project."
    """

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            print("Warning: GOOGLE_API_KEY not found. Jules will be offline.")
            self.model = None
            return

        genai.configure(api_key=self.api_key)

        # Initialize Gemini 1.5 Pro (current Pro model)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        self.chat = self.model.start_chat(history=[
            {"role": "user", "parts": [self.SYSTEM_PROMPT]},
            {"role": "model", "parts": ["Understood. I am Jules, ready to assist with Turtle Terminal strategies within the strict project context."]}
        ])

    async def ask(self, message: str) -> str:
        if not self.model:
            return "Jules is offline. Please configure GOOGLE_API_KEY."

        try:
            # Send message to chat session
            response = self.chat.send_message(message)
            return response.text
        except Exception as e:
            return f"Error communicating with Gemini: {str(e)}"
