import os
import google.generativeai as genai
from typing import Optional

class JulesAssistant:
    """
    Jules: The Turtle Terminal AI Assistant.
    Powered strictly by Google Gemini Pro (gemini-1.5-pro).
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

        # Try to initialize with preferred models in order
        models_to_try = ['gemini-1.5-pro', 'gemini-pro']
        self.model = None

        for model_name in models_to_try:
            try:
                print(f"Attempting to initialize Jules with model: {model_name}...")
                model = genai.GenerativeModel(model_name)

                # Test chat to ensure it works
                chat = model.start_chat(history=[
                    {"role": "user", "parts": [self.SYSTEM_PROMPT]},
                    {"role": "model", "parts": ["Understood. I am Jules, ready to assist with Turtle Terminal strategies within the strict project context."]}
                ])

                # If we get here, it worked
                self.model = model
                self.chat = chat
                print(f"Jules successfully initialized with {model_name}")
                break
            except Exception as e:
                print(f"Failed to initialize {model_name}: {e}")

        if not self.model:
            print("Jules initialization failed for all attempted models.")
            # Try to list models if possible to aid debugging
            try:
                found_models = []
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        found_models.append(m.name)
                print(f"Available models: {found_models}")
            except Exception as le:
                print(f"Failed to list models: {le}")

    async def ask(self, message: str) -> str:
        if not self.model:
            # Try re-initializing in case API key was added at runtime
            self.initialize()
            if not self.model:
                return "Jules is offline. Please configure GOOGLE_API_KEY or check model availability."

        try:
            # Send message to chat session
            response = self.chat.send_message(message)
            return response.text
        except Exception as e:
            return f"Error communicating with Gemini: {str(e)}"
