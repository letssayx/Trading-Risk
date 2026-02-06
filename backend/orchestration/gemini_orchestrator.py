from typing import Dict, Any

class GeminiOrchestrator:
    """
    Mock AI orchestrator to translate NL to Strategy Config/Code.
    In prod, this calls Google Gemini API.
    """

    def translate_to_logic(self, user_input: str) -> Dict[str, Any]:
        """
        Parses natural language and returns a config dict + python code string.
        Uses a prompt template mimicking the role of a Senior Quantitative Developer.
        """
        print(f"Gemini Processing: '{user_input}'")

        # System Prompt Template (For real Gemini call)
        system_prompt = """
ACT AS: A Senior Quantitative Developer specialized in Python and Technical Analysis.

TASK: Translate the User's Natural Language trading strategy into a structured JSON object.

OUTPUT FORMAT: Return ONLY a JSON object with two keys:
1. "config": A dictionary of the parameters (e.g., periods, thresholds).
2. "python_code": A valid Python string implementing the 'BaseStrategy' class.

CODE CONSTRAINTS:
- Use 'numpy' and 'pandas' for all calculations.
- The class must implement: `compute_indicators(self, data)` and `check_signals(self, data)`.
- Use deterministic logic; do not include any LLM-based reasoning inside the 'python_code'.
- Ensure the code is compatible with Python 3.11+.
- Assume 'data' is a pandas DataFrame with columns: [time, open, high, low, close, volume, iv].

USER INPUT: "{user_input}"
        """

        # Mock Response Logic based on keywords
        target = "NIFTY" if "Nifty" in user_input else "UNK"
        rsi_val = 30 # Default/Mock

        # For verification purposes, we return a valid Python structure matching BaseStrategy
        python_code = f"""
from backend.strategies.base_strategy import BaseStrategy
import pandas as pd
import numpy as np

class AIStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("AI_RSI_Strategy", config={{"rsi_period": 14, "oversold": {rsi_val}}})
        self.rsi_period = 14
        self.oversold = {rsi_val}

    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        return df

    def check_signals(self, df: pd.DataFrame, current_pos: dict) -> str:
        if df.empty: return "HOLD"

        rsi = df['RSI'].iloc[-1]
        is_long = current_pos.get('quantity', 0) > 0

        if rsi < self.oversold and not is_long:
            return "BUY"
        elif rsi > 70 and is_long:
            return "SELL"

        return "HOLD"

    def youtube(self):
        pass
"""
        return {
            "config": {"target": target, "parameters": {"rsi_period": 14, "oversold": rsi_val}},
            "python_code": python_code
        }
