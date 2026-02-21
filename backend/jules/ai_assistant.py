import os
import google.generativeai as genai
from typing import Optional

class JulesAssistant:
    """
    Jules: The Turtle Terminal AI Assistant.
    Powered strictly by Google Gemini Pro (gemini-pro).
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
        self.model = None
        self.chat = None
        self.initialize()

    def initialize(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            print("Warning: GOOGLE_API_KEY not found. Jules will be offline.")
            self.model = None
            return

        genai.configure(api_key=self.api_key)

        try:
            # Enforce gemini-pro
            model_name = 'gemini-pro'
            print(f"Initializing Jules with model: {model_name}...")

            self.model = genai.GenerativeModel(model_name)

            # Start Chat Session
            self.chat = self.model.start_chat(history=[
                {"role": "user", "parts": [self.SYSTEM_PROMPT]},
                {"role": "model", "parts": ["Understood. I am Jules, ready to assist with Turtle Terminal strategies within the strict project context."]}
            ])

            print(f"Jules successfully initialized with {model_name}")

        except Exception as e:
            print(f"Failed to initialize Jules ({model_name}): {e}")
            self.model = None

    async def ask(self, message: str) -> str:
        # Check if initialized, try re-init if not (runtime key update)
        if not self.model:
            self.initialize()

        if not self.model:
            return "Jules is offline. Please configure GOOGLE_API_KEY or check model availability."

        try:
            # Send message to chat session
            response = self.chat.send_message(message)
            return response.text
        except Exception as e:
            # If error is about model not found, try to list models for debugging context in logs
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg:
                try:
                    models = [m.name for m in genai.list_models()]
                    print(f"Available models: {models}")
                except:
                    pass
            return f"Error communicating with Gemini: {error_msg}"
