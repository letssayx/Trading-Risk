import os
import google.generativeai as genai
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class JulesAssistant:
    def __init__(self):
        self.model = None
        self._load_key()

    def _load_key(self):
        # Reload key from file/env
        load_dotenv(override=True)
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self._select_best_model()
        else:
            self.model = None
            logger.warning("Jules: No Google API Key found.")

    def _select_best_model(self):
        """
        Dynamically selects the best available model for generateContent.
        """
        try:
            available_models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)

            logger.info(f"Jules: Available Models: {available_models}")

            # Preference list
            preferences = [
                'models/gemini-1.5-flash',
                'models/gemini-1.5-pro',
                'models/gemini-pro',
                'models/gemini-1.0-pro'
            ]

            selected = None

            # 1. Try preferences first
            for pref in preferences:
                if pref in available_models:
                    selected = pref
                    break

            # 2. If no preference found, pick the first available 'gemini' model
            if not selected:
                for m in available_models:
                    if 'gemini' in m:
                        selected = m
                        break

            # 3. Fallback to anything
            if not selected and available_models:
                selected = available_models[0]

            if selected:
                logger.info(f"Jules: Selected Model -> {selected}")
                self.model = genai.GenerativeModel(selected)
            else:
                logger.error("Jules: No suitable model found in list.")
                # Fallback to hardcoded if list fails (e.g. permission issue on list)
                self.model = genai.GenerativeModel('gemini-1.5-flash')

        except Exception as e:
            logger.error(f"Jules: Error listing models: {e}")
            # Fallback
            self.model = genai.GenerativeModel('gemini-1.5-flash')

    async def get_response(self, message: str) -> str:
        # Always reload key before request to catch config changes
        if not self.model:
             self._load_key()

        if not self.model:
            return "Please configure your Google API Key in Settings to use Jules."

        try:
            # System Prompt to enforce context and format
            system_instruction = (
                "You are Jules, an AI Assistant for the Turtle Terminal trading platform. "
                "Your role is to assist with quantitative finance, python coding for strategies, and market analysis. "
                "Do NOT answer questions unrelated to finance, coding, or the platform. "
                "If you write Python code, enclose it strictly within ```python ... ``` blocks. "
                "Do not simulate data exchange. Assume the user has the data locally or will load it."
            )

            # Since Gemini Pro stateless chat might not support system instructions directly in start_chat in all versions,
            # we prepend it to the first message or use history.
            history = [
                {"role": "user", "parts": [system_instruction]},
                {"role": "model", "parts": ["Understood. I am Jules, ready to assist with Turtle Terminal."]}
            ]

            chat = self.model.start_chat(history=history)
            response = await chat.send_message_async(message)
            return response.text
        except Exception as e:
            logger.error(f"Jules: Generation Error: {e}")
            return f"I encountered an error: {str(e)}"

# Singleton instance
jules = JulesAssistant()
