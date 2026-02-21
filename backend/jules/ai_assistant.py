import os
import google.generativeai as genai
import asyncio

class JulesAssistant:
    def __init__(self, provider="gemini"):
        self.provider = "gemini"
        self.gemini_model = None
        self._configure()

    def _configure(self):
        """Try to configure the model from environment variables."""
        self.google_key = os.getenv("GOOGLE_API_KEY")
        if self.google_key:
            try:
                genai.configure(api_key=self.google_key)
                self.gemini_model = genai.GenerativeModel('gemini-pro')
            except Exception as e:
                print(f"Jules Init Error: {e}")
                self.gemini_model = None
        else:
             # Silent warning, will retry on ask
             pass

    async def ask(self, prompt: str) -> str:
        """
        Generic ask method restricted to Project and Strategies.
        Lazy-loads configuration if missing.
        """
        # Retry configuration if model is not ready (e.g. key added at runtime)
        if not self.gemini_model:
            self._configure()

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
            # Use 'generate_content_async' if available, else sync wrapped in thread?
            # google.generativeai usually supports async
            response = await self.gemini_model.generate_content_async(full_prompt)
            return response.text
        except Exception as e:
            return f"Error from Gemini: {str(e)}"
