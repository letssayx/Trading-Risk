import os
import google.generativeai as genai
import asyncio

class JulesAssistant:
    def __init__(self, provider="gemini"):
        # Enforce Gemini as primary per user request
        self.provider = "gemini"

        # Try to load keys
        self.google_key = os.getenv("GOOGLE_API_KEY")

        if not self.google_key:
             print("Warning: Google API Key missing for Jules (Gemini). Chat may fail.")

        # Initialize Clients
        if self.provider == "gemini":
            if self.google_key:
                genai.configure(api_key=self.google_key)
                self.gemini_model = genai.GenerativeModel('gemini-pro')
            else:
                self.gemini_model = None

    async def ask(self, prompt: str) -> str:
        """
        Generic ask method restricted to Project and Strategies.
        """
        if not self.gemini_model:
            # Retry configuration if key was added runtime
            self.google_key = os.getenv("GOOGLE_API_KEY")
            if self.google_key:
                try:
                    genai.configure(api_key=self.google_key)
                    self.gemini_model = genai.GenerativeModel('gemini-pro')
                except:
                    pass

        if not self.gemini_model:
            return "Error: Jules (Gemini) is not configured. Please add GOOGLE_API_KEY in Config."

        system_instruction = """
        You are Jules, a specialized quantitative trading assistant for the 'Turtle Terminal' project.
        Your scope is strictly limited to:
        1. Explaining the codebase and architecture of this project.
        2. Assisting with trading strategies (Turtle, StatArb, Volatility, etc.).
        3. Helping implement strategies as Python plugins.
        4. Analyzing market data provided in the context.

        Do not answer general knowledge questions unrelated to trading or coding.
        If asked about off-topic matters, politely redirect to trading strategies.
        """

        full_prompt = f"{system_instruction}\n\nUser: {prompt}\nJules:"

        try:
            response = await self.gemini_model.generate_content_async(full_prompt)
            return response.text
        except Exception as e:
            return f"Error from Gemini: {str(e)}"
