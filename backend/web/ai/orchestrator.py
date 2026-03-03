import asyncio
import json
import re
from typing import Dict, Any, Optional, Callable
from sqlalchemy.orm import Session
from groq import AsyncGroq
from google import genai
from openai import AsyncOpenAI  # Used for OpenRouter
from backend.web.ai.tools import fetch_bhavcopy_data
from backend.ingest.nse_models import AIPrediction

class TerminalOrchestrator:
    def __init__(self, groq_key: str, openrouter_key: str, gemini_key: str, db: Session, session_id: str):
        self.groq_client = AsyncGroq(api_key=groq_key)
        self.openrouter_client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key,
        )
        self.gemini_client = genai.Client(api_key=gemini_key)
        self.db = db
        self.session_id = session_id

        # We pass stream=True implicitly in the client calls or we just wrap it for Groq

    async def step1_dispatch(self, command: str) -> str:
        """Uses Llama 3.3 to classify the command into an Engine type."""
        prompt = f"""
        Classify the following trading command into exactly one of these 5 categories:
        1. Black Swan
        2. Macro
        3. Corporate Action
        4. Derivatives
        5. Earnings

        Command: "{command}"

        Return ONLY the exact category name. Nothing else.
        """
        response = await self.groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.0,
            max_completion_tokens=10
        )
        engine_type = response.choices[0].message.content.strip()
        # Clean up any surrounding punctuation
        for val in ["Black Swan", "Macro", "Corporate Action", "Derivatives", "Earnings"]:
            if val.lower() in engine_type.lower():
                return val
        return "Derivatives" # Fallback

    async def step2_data_clerk(self, command: str, engine_type: str) -> Dict[str, Any]:
        """Uses Qwen 2.5 (OpenRouter) to extract ticker and fetch real data."""
        # 1. Extract Ticker
        prompt = f"""
        Extract the NSE stock ticker symbol from this command.
        If it's an index, return NIFTY or BANKNIFTY.
        If no ticker is found, return "NIFTY".
        Command: "{command}"
        Return ONLY the ticker string in uppercase.
        """
        try:
            response = await self.openrouter_client.chat.completions.create(
                model="qwen/qwen-2.5-coder-32b-instruct",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                extra_headers={
                    "HTTP-Referer": "https://turtle-terminal.local",
                    "X-Title": "Turtle Terminal",
                    "X-Zero-Retention": "true" # Professional Data Handling
                }
            )
            ticker = response.choices[0].message.content.strip().upper()
            # Clean ticker
            ticker = re.sub(r'[^A-Z0-9-]', '', ticker)
            if not ticker: ticker = "NIFTY"
        except Exception as e:
            ticker = "NIFTY"

        # 2. Fetch Real Data (Zero Hallucination)
        real_data = fetch_bhavcopy_data(self.db, ticker)
        return real_data

    async def step3_quant_logic(self, command: str, engine_type: str, data_matrix: Dict[str, Any], callback: Callable):
        """Uses Llama 3.3 (Groq) to stream reasoning logic."""
        prompt = f"""
        You are a quantitative trading logic engine analyzing a {engine_type} event.
        Command: {command}

        Real Data Context:
        {json.dumps(data_matrix, indent=2)}

        Do not invent or assume current prices. Use the Real Data Context provided above.
        Think step-by-step about the market implications.
        Use the <think> tags to show your math and logic.
        """

        stream = await self.groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            stream=True
        )

        full_reasoning = ""
        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                token = chunk.choices[0].delta.content
                full_reasoning += token
                await callback(token)

        return full_reasoning

    async def step4_strategist(self, command: str, engine_type: str, data_matrix: Dict[str, Any], reasoning: str) -> Dict[str, Any]:
        """Uses Gemini 1.5 Pro to synthesize the final execution card."""
        prompt = f"""
        You are the Head Strategist for a Hedge Fund.

        Scenario: {command}
        Engine: {engine_type}

        Real Data (Do not invent numbers outside of this):
        {json.dumps(data_matrix, indent=2)}

        Quant Reasoning:
        {reasoning}

        Provide a final execution recommendation. You must return your response as a strict JSON object with EXACTLY these keys:
        - "action": string (e.g., "ACCUMULATE ON DIPS", "AGGRESSIVE SHORT", "HOLD")
        - "target": float (the numerical price target)
        - "stop_loss": float (the numerical stop loss)
        - "confidence": integer (0 to 100 representing confidence score)
        - "predicted_price": float (your predicted opening price for the next session)
        - "rationale": string (a 1-2 sentence explanation)

        Output ONLY valid JSON.
        """

        models_to_try = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.5-pro-latest']
        response = None
        text = ""

        for model_name in models_to_try:
            try:
                response = await self.gemini_client.aio.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                text = response.text
                break
            except Exception as e:
                # If it's a 404 or unsupported model error, try the next one
                if "404" in str(e) or "NOT_FOUND" in str(e):
                    continue
                # If it's another error, we might still want to try the next model just in case
                continue

        if not response:
            return {
                "action": "ERROR SYNTHESIZING",
                "target": 0.0,
                "stop_loss": 0.0,
                "confidence": 0,
                "predicted_price": 0.0,
                "rationale": "Failed to generate content: All Gemini fallback models resulted in 404 NOT_FOUND or other errors. Please check your API Key and model permissions."
            }

        # Clean JSON
        try:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                text = match.group(0)
            exec_data = json.loads(text)

            # Persist to DB
            pred = AIPrediction(
                session_id=self.session_id,
                ticker=data_matrix.get("ticker", "NIFTY"),
                engine_type=engine_type,
                predicted_price=float(exec_data.get("predicted_price", 0)),
                action=exec_data.get("action", ""),
                target=float(exec_data.get("target", 0)),
                stop_loss=float(exec_data.get("stop_loss", 0)),
                confidence=int(exec_data.get("confidence", 0)),
                rationale=exec_data.get("rationale", "")
            )
            self.db.add(pred)
            self.db.commit()

            return exec_data
        except Exception as e:
            # Fallback
            return {
                "action": "ERROR SYNTHESIZING",
                "target": 0.0,
                "stop_loss": 0.0,
                "confidence": 0,
                "predicted_price": 0.0,
                "rationale": f"Failed to parse Gemini output: {str(e)}"
            }
