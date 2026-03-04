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

    async def step0_persona_prefilter(self, command: str) -> str:
        """Uses Gemini to deeply reason about the user's raw command and convert it into a detailed quant task."""
        prompt = f"""
        You are 'Jules', the expert UI/UX Logic model for a hedge fund terminal.
        A trader has entered the following command: "{command}"

        Your task is to convert this raw command into a detailed, strict, step-by-step task instructions for the backend quant engines.
        You must use deep logical deliberate reasoning and chain of thought (think through a feedback loop internally).
        You can output your internal reasoning first if needed, but the final task must be clearly separated.
        Actually, just output ONLY the final detailed task description to avoid breaking the pipeline, but ensure your generation process is deliberate.
        Ensure you explicitly instruct the downstream models to use quant grade logic, strictly no hallucination, no fake data, and no false assumptions.

        Example Output Format:
        Task - You are an expert derivatives strategist. Use step-by-step reasoning to analyze [Subject].
        Analyze:
        a. Calculate a theoretical opening price based on a [Model type] shock.
        b. Provide a final predicted opening price range.
        Output - strictly no hallucination, no fake data, no false assumptions.
        """

        models_to_try = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']
        text = command # Default to original command if it fails

        for model_name in models_to_try:
            try:
                response = await self.gemini_client.aio.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                if response and response.text:
                    text = response.text.strip()
                break
            except Exception:
                continue

        return text

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
        You must use deep logical deliberate reasoning and chain of thought (think through a feedback loop internally) before answering.
        If it's an index, return NIFTY or BANKNIFTY.
        If no ticker is found, return "NONE".
        Command: "{command}"
        Your output should ONLY contain the final ticker string in uppercase (or NONE). No other text.
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
            if not ticker: ticker = "NONE"
        except Exception as e:
            ticker = "NONE"

        # 2. Fetch Real Data (Zero Hallucination)
        real_data = fetch_bhavcopy_data(self.db, ticker)
        return real_data

    async def step3_quant_logic(self, command: str, engine_type: str, callback: Callable):
        """Uses Llama 3.3 (Groq) to stream reasoning logic."""
        prompt = f"""
        You are a quantitative trading logic engine analyzing a {engine_type} event.
        Command: {command}

        CRITICAL INSTRUCTIONS:
        1. You MUST use deep logical deliberate reasoning and chain of thought (think through a feedback loop internally).
        2. DO NOT invent, assume, or guess specific current stock prices, index levels, or numerical targets.
        3. DO NOT perform arithmetic on assumed prices.
        4. Your role is strictly to provide directional market reasoning, sector impact analysis, and qualitative logic.
        5. The final numerical calculations will be handled by the Execution Strategist in the next step using real database values.

        Think step-by-step about the broader market implications and directional sentiment.
        Always output your internal reasoning explicitly inside `<think>` ... `</think>` tags before your final response.
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

        You must use deep logical deliberate reasoning and chain of thought (think through a feedback loop internally) before deciding on the execution card.
        You can output your thought process first inside `<reasoning>` tags.
        After your reasoning, provide a final execution recommendation as a strict JSON object with EXACTLY these keys:
        - "action": string (e.g., "ACCUMULATE ON DIPS", "AGGRESSIVE SHORT", "HOLD")
        - "target": float (the numerical price target)
        - "stop_loss": float (the numerical stop loss)
        - "confidence": integer (0 to 100 representing confidence score)
        - "predicted_price": float (your predicted opening price for the next session)
        - "rationale": string (a 1-2 sentence explanation)

        The final output MUST contain this valid JSON block.
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

    async def step5_compliance_judge(self, command: str, data_matrix: Dict[str, Any], reasoning: str, exec_card: Dict[str, Any]) -> Dict[str, Any]:
        """Uses Llama 3.3 to verify the logic and data integrity (Compliance Judge)."""

        # Deterministic checks
        try:
            action = str(exec_card.get("action", "")).upper()
            target = float(exec_card.get("target", 0.0))

            # Fetch current close price to do deterministic check
            current_price = 0.0
            if data_matrix.get("equity") and data_matrix["equity"].get("close_price"):
                current_price = float(data_matrix["equity"]["close_price"])
            elif data_matrix.get("futures") and data_matrix["futures"].get("close_price"):
                current_price = float(data_matrix["futures"]["close_price"])

            if current_price > 0.0:
                if "BUY" in action or "ACCUMULATE" in action or "LONG" in action:
                    if target > 0 and target <= current_price:
                        return {"status": "FAIL", "critique": f"Deterministic failure: Action is {action} but target price {target} is not greater than current price {current_price}."}
                elif "SELL" in action or "SHORT" in action:
                    if target > 0 and target >= current_price:
                        return {"status": "FAIL", "critique": f"Deterministic failure: Action is {action} but target price {target} is not less than current price {current_price}."}
        except Exception as e:
            # If deterministic checks fail to parse numbers, we let the LLM Judge handle it.
            pass

        # LLM Judge
        prompt = f"""
        You are the Compliance Judge for a Hedge Fund's AI trading system.
        Your job is to verify that the Strategist's Output (Execution Card) strictly adheres to the Real Data and Quant Reasoning.

        Real Data JSON:
        {json.dumps(data_matrix, indent=2)}

        Quant Reasoning:
        {reasoning}

        Strategist's Output:
        {json.dumps(exec_card, indent=2)}

        Check for the following:
        1. Hallucination Jump: Does the Strategist's rationale contradict the Quant's step-by-step logic?
        2. Data Verification: Are the numbers in the Output consistent with the Real Data JSON? (e.g., target price must be somewhat realistic based on current prices, OI numbers cited must match Data Matrix).
        3. Safety Guardrails: If there are major discrepancies or missing data, flag it.

        You MUST use deep logical deliberate reasoning and chain of thought (think through a feedback loop internally) before reaching your conclusion.
        Output your logic first inside `<reasoning>` tags.

        Then, return a strict JSON response with exactly these keys:
        - "status": string ("PASS" or "FAIL")
        - "critique": string (If FAIL, explain exactly what the error is and how the Strategist should fix it. If PASS, leave empty string.)

        Your final output MUST contain this valid JSON block.
        """

        try:
            response = await self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.0,
                extra_headers={
                    "X-Zero-Retention": "true"
                }
            )
            text = response.choices[0].message.content.strip()

            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                text = match.group(0)

            judge_res = json.loads(text)
            return judge_res
        except Exception as e:
            # If the judge fails to parse or respond, we fail safely to trigger a retry
            return {"status": "FAIL", "critique": f"Compliance Judge encountered an error checking output: {str(e)}"}

    async def step6_persona_filter(self, exec_card: Dict[str, Any]) -> Dict[str, Any]:
        """Uses Gemini to rewrite the execution card into a Quant Desk tone."""
        prompt = f"""
        You are 'Jules', a seasoned hedge fund quant desk UI/UX model.
        Rewrite the following trading execution output to have a professional, highly concise 'Quant Desk' tone.
        Remove wordy, robotic phrases. Ensure the formatting is actionable, highlighting the critical signal.

        Original Input:
        {json.dumps(exec_card, indent=2)}

        You MUST use deep logical deliberate reasoning and chain of thought (think through a feedback loop internally) to determine the best phrasing.
        You can output your internal thought process inside `<reasoning>` tags.
        Then, return a strict JSON object with the exact same keys:
        - "action": string
        - "target": float
        - "stop_loss": float
        - "confidence": integer
        - "predicted_price": float
        - "rationale": string (Rewrite this to be a short, sharp quant desk note, e.g., "High conviction on IDFC; OI surge confirmed").

        Your final output MUST contain this valid JSON block.
        """

        models_to_try = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']
        text = ""

        for model_name in models_to_try:
            try:
                response = await self.gemini_client.aio.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                text = response.text
                break
            except Exception:
                continue

        try:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                text = match.group(0)
            final_card = json.loads(text)

            return final_card
        except Exception as e:
            # If formatting fails, just return the original card so we don't break the UI
            return exec_card
