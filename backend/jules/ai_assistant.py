import os
import ast
import json
import logging
from typing import Optional, Dict, Any
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from backend.config import settings
from backend.jules.strategy_parser import StrategyParser

logger = logging.getLogger(__name__)

class JulesAssistant:
    """
    AI Assistant for generating Python strategies and answering queries.
    Uses Google Gemini (Primary), OpenAI, or Groq via SDKs.
    Includes Quality Control loop and Tenacity retries.
    """

    def __init__(self):
        self.google_key = settings.GOOGLE_API_KEY
        self.openai_key = settings.OPENAI_API_KEY
        self.groq_key = settings.GROQ_API_KEY
        self.fallback_parser = StrategyParser()

        self._configure_providers()

    def _configure_providers(self):
        if self.google_key:
            try:
                genai.configure(api_key=self.google_key)
                self.gemini_model = genai.GenerativeModel('gemini-pro')
            except Exception as e:
                logger.error(f"Failed to configure Gemini: {e}")
                self.google_key = None # Disable if failed

    def query(self, prompt: str, context: Optional[Dict] = None) -> str:
        """
        General purpose query handler.
        """
        system_prompt = "You are Jules, an expert quantitative developer for the Turtle Terminal. Answer concisely and technically."
        if context:
            system_prompt += f"\nContext: {json.dumps(context)}"

        return self._call_llm(system_prompt, prompt)

    def generate_strategy(self, prompt: str) -> Dict[str, Any]:
        """
        Generates both executable code (via LLM) and structured config (via Parser).
        """
        # 1. Generate Config (Deterministic) for Visualization
        config = self.fallback_parser.parse(prompt)

        # 2. Generate Code (LLM with Quality Control)
        code = self.generate_code(prompt)

        return {
            "code": code,
            "config": config
        }

    def generate_code(self, prompt: str) -> str:
        """
        Generates Python strategy code with Quality Control loop.
        """
        system_prompt = (
            "You are a Python Strategy Generator for Turtle Terminal.\n"
            "Output ONLY valid Python code. No markdown, no explanations.\n"
            "Assume `backend` package is available.\n"
            "The code should define a `strategy` variable or class instance.\n"
            "Do NOT use `input()` or interactive functions."
        )

        # 1. Try LLM Generation
        try:
            code = self._call_llm(system_prompt, prompt)
        except Exception as e:
            logger.error(f"LLM Generation Failed: {e}")
            code = "LLM_ERROR"

        # Fallback
        if "LLM_NOT_CONFIGURED" in code or "LLM_ERROR" in code or not code.strip():
            logger.info("Falling back to rule-based parser")
            parsed = self.fallback_parser.parse(prompt)
            return self.fallback_parser.generate_code(parsed)

        # 2. Quality Control Loop
        max_retries = 3
        for attempt in range(max_retries):
            # Clean formatting
            code = self._clean_code(code)

            error = self._validate_syntax(code)
            if not error:
                return code

            logger.warning(f"Syntax Error (Attempt {attempt+1}): {error}")

            # Self-Correction
            fix_prompt = (
                f"The following code has a syntax error: {error}\n"
                f"Code:\n{code}\n"
                "Please fix the syntax and return ONLY the corrected code."
            )
            try:
                code = self._call_llm(system_prompt, fix_prompt)
            except Exception:
                break # Stop if fix fails

        return f"# Error: Could not generate valid code.\n# Last Error: {error}\n\n{code}"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10),
           retry=retry_if_exception_type(Exception))
    def _call_llm(self, system: str, user: str) -> str:
        """
        Dispatches to available LLM provider using SDKs.
        Prioritizes Google Gemini.
        """
        if self.google_key:
            return self._call_gemini(system, user)
        elif self.openai_key:
            return self._call_openai(system, user)
        elif self.groq_key:
            return self._call_groq(system, user)
        else:
            return "LLM_NOT_CONFIGURED"

    def _call_gemini(self, system: str, user: str) -> str:
        # Gemini Pro doesn't separate system/user in the same way as Chat completions.
        # We combine them.
        full_prompt = f"{system}\n\nUser Request: {user}"
        response = self.gemini_model.generate_content(full_prompt)
        return response.text

    def _call_openai(self, system: str, user: str) -> str:
        # Lazy import to avoid hard dependency if not used
        import openai
        client = openai.OpenAI(api_key=self.openai_key, timeout=30.0)
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content

    def _call_groq(self, system: str, user: str) -> str:
        # Lazy import
        from groq import Groq
        client = Groq(api_key=self.groq_key, timeout=30.0)
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            model="llama3-70b-8192",
        )
        return chat_completion.choices[0].message.content

    def _validate_syntax(self, code: str) -> Optional[str]:
        try:
            ast.parse(code)
            return None
        except SyntaxError as e:
            return str(e)
        except Exception as e:
            return str(e)

    def _clean_code(self, text: str) -> str:
        """Removes markdown code blocks."""
        if "```python" in text:
            text = text.split("```python")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return text.strip()
