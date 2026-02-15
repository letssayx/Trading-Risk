import os
import ast
import json
import logging
import requests
from typing import Optional, Dict, Any
from backend.config import settings
from backend.jules.strategy_parser import StrategyParser

logger = logging.getLogger(__name__)

class JulesAssistant:
    """
    AI Assistant for generating Python strategies and answering queries.
    Wraps LLM calls (OpenAI/Anthropic) via REST to avoid dependencies.
    Includes Quality Control loop for code generation.
    """

    def __init__(self):
        self.openai_key = settings.OPENAI_API_KEY
        self.anthropic_key = settings.ANTHROPIC_API_KEY
        self.fallback_parser = StrategyParser()

    def query(self, prompt: str, context: Optional[Dict] = None) -> str:
        """
        General purpose query handler.
        """
        system_prompt = "You are Jules, an expert quantitative developer. Answer concisely."
        if context:
            system_prompt += f"\nContext: {json.dumps(context)}"

        return self._call_llm(system_prompt, prompt)

    def generate_strategy(self, prompt: str) -> Dict[str, Any]:
        """
        Generates both executable code (via LLM) and structured config (via Parser).
        Ensures frontend visualization works while providing robust code.
        """
        # 1. Generate Config (Deterministic) for Visualization
        # This allows the Strategy Composer to render nodes even if LLM code is complex
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
        # 1. Try LLM Generation
        system_prompt = (
            "You are a Python Strategy Generator for Turtle Terminal.\n"
            "Output ONLY valid Python code. No markdown, no explanations.\n"
            "Assume `backend` package is available.\n"
            "The code should define a `strategy` variable or class instance."
        )

        code = self._call_llm(system_prompt, prompt)

        # Fallback if LLM fails or is not configured
        if "LLM_NOT_CONFIGURED" in code or not code.strip():
            logger.info("Falling back to rule-based parser")
            # Use the existing deterministic parser logic
            parsed = self.fallback_parser.parse(prompt)
            return self.fallback_parser.generate_code(parsed)

        # 2. Quality Control Loop
        max_retries = 3
        for attempt in range(max_retries):
            error = self._validate_syntax(code)
            if not error:
                return code

            logger.warning(f"Syntax Error in generated code (Attempt {attempt+1}): {error}")

            # Self-Correction
            fix_prompt = (
                f"The following code has a syntax error: {error}\n"
                f"Code:\n{code}\n"
                "Please fix the syntax and return ONLY the corrected code."
            )
            code = self._call_llm(system_prompt, fix_prompt)

        # If still failing, return commented error
        return f"# Error: Could not generate valid code after {max_retries} attempts.\n# Last Error: {error}\n\n{code}"

    def _validate_syntax(self, code: str) -> Optional[str]:
        """
        Checks if code is valid Python syntax using ast.
        Returns error message or None.
        """
        try:
            ast.parse(code)
            return None
        except SyntaxError as e:
            return str(e)
        except Exception as e:
            return str(e)

    def _call_llm(self, system: str, user: str) -> str:
        """
        Dispatches to available LLM provider via REST.
        """
        if self.openai_key:
            return self._call_openai(system, user)
        elif self.anthropic_key:
            return self._call_anthropic(system, user)
        else:
            return "LLM_NOT_CONFIGURED"

    def _call_openai(self, system: str, user: str) -> str:
        try:
            headers = {
                "Authorization": f"Bearer {self.openai_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-4-turbo",  # or gpt-3.5-turbo
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                "temperature": 0.2
            }
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            # Strip markdown fences if present
            return self._clean_code(content)
        except Exception as e:
            logger.error(f"OpenAI Call Failed: {e}")
            return ""

    def _call_anthropic(self, system: str, user: str) -> str:
        try:
            headers = {
                "x-api-key": self.anthropic_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "claude-3-opus-20240229",
                "system": system,
                "messages": [
                    {"role": "user", "content": user}
                ],
                "max_tokens": 4096,
                "temperature": 0.2
            }
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            content = response.json()["content"][0]["text"]
            return self._clean_code(content)
        except Exception as e:
            logger.error(f"Anthropic Call Failed: {e}")
            return ""

    def _clean_code(self, text: str) -> str:
        """Removes markdown code blocks if present."""
        if "```python" in text:
            text = text.split("```python")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return text.strip()
