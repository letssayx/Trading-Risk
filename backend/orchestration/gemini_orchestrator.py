from typing import Dict, Any

class GeminiOrchestrator:
    """
    Mock AI orchestrator to translate NL to Strategy Config/Code.
    In prod, this calls Google Gemini API.
    """

    def translate_to_logic(self, user_input: str) -> Dict[str, Any]:
        """
        Parses natural language and returns a config dict + python code string.
        """
        print(f"Gemini Processing: '{user_input}'")

        # Mock Logic: Simple keyword extraction
        target = "NIFTY" if "Nifty" in user_input else "UNK"
        rsi_val = 30 # Mock extraction

        config = {
            "target": target,
            "indicators": ["RSI"],
            "parameters": {"rsi_period": 14, "oversold": rsi_val}
        }

        python_code = f"""
from backend.strategies.base_strategy import BaseStrategy
import pandas as pd

class AIStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("AI_RSI_Strategy")
        self.rsi_period = 14
        self.oversold = {rsi_val}

    def compute_indicators(self, df):
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        return df

    def check_signals(self, df, pos):
        if df['RSI'].iloc[-1] < self.oversold:
            return "BUY"
        return "HOLD"

    def youtube(self):
        print("Strategy Explanation Video...")
"""
        return {
            "config": config,
            "python_code": python_code
        }
