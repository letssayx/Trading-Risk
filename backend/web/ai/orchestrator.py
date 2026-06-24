import json
import re
from typing import Dict, Any, Callable
from sqlalchemy.orm import Session
from groq import AsyncGroq
from google import genai
from openai import AsyncOpenAI  # Used for OpenRouter
from backend.web.ai.tools import fetch_bhavcopy_data, search_db_symbol, search_yfinance_symbol, fetch_detailed_db_data, fetch_yfinance_historical

class TerminalOrchestrator:
    def __init__(self, groq_key: str, openrouter_key: str, gemini_key: str, db: Session, session_id: str):
        self.groq_client = AsyncGroq(api_key=groq_key)
        self.openrouter_client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key,
        )
        self.gemini_client = genai.Client(
            api_key=gemini_key,
            http_options={'api_version': 'v1'}
        )
        self.db = db
        self.session_id = session_id

        # We pass stream=True implicitly in the client calls or we just wrap it for Groq

    async def step0_persona_prefilter(self, command: str) -> Dict[str, str]:
        """Uses Gemini to deeply reason about the user's raw command and convert it into a detailed quant task."""
        prompt = f"""
        A trader has entered the following command: "{command}"

        Your task is to convert this raw command into a concise, direct task instruction for a quantitative trading engine.
        Do NOT include boilerplate phrasing like "You are an expert...". Just provide the direct mathematical or logical steps required.
        You must use deep logical deliberate reasoning and chain of thought (think through a feedback loop internally).
        Output your internal reasoning first inside `<reasoning>` tags.

        Then, output a strict JSON object with exactly these keys:
        - "task": string (The concise, direct task instruction).

        Example JSON Output:
        {{
            "task": "Analyze [Subject]. Calculate a theoretical opening price based on recent volatility and open interest. Output trade execution target and stop loss."
        }}

        Your final output MUST contain this valid JSON block.
        """

        models_to_try = ['gemini-1.5-flash', 'gemini-2.0-flash']
        text = ""
        error_msg = ""

        for model_name in models_to_try:
            try:
                response = await self.gemini_client.aio.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                if response and response.text:
                    text = response.text.strip()
                break
            except Exception as e:
                error_msg = str(e)
                continue

        if not text:
            # Fallback to Llama 3 on Groq
            try:
                fallback_response = await self.groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                if fallback_response and fallback_response.choices and fallback_response.choices[0].message.content:
                    text = fallback_response.choices[0].message.content.strip()
            except Exception as e:
                return {
                    "task": command,
                    "reasoning": f"Failed to generate task via Gemini ({error_msg}) AND Llama 3 fallback ({str(e)}). Proceeding with raw command."
                }

        reasoning = ""
        reasoning_match = re.search(r'<reasoning>(.*?)</reasoning>', text, re.DOTALL | re.IGNORECASE)
        if reasoning_match:
            reasoning = reasoning_match.group(1).strip()

        try:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                text = match.group(0)
            result = json.loads(text)
            return {
                "task": result.get("task", command),
                "reasoning": reasoning
            }
        except Exception as e:
            return {
                "task": command,
                "reasoning": reasoning + f"\n\nJSON Parse Error: {str(e)}. Proceeding with raw command."
            }

    async def step1_dispatch(self, command: str, history: list = None) -> str:
        """Uses Gemini to classify the command into an analysis intent."""

        history_summary = ""
        if history and len(history) > 0:
            history_summary = "\nRecent Conversation History:\n"
            for msg in history[-3:]:
                history_summary += f"{msg.get('role', 'unknown').capitalize()}: {msg.get('content', '')[:100]}...\n"

        prompt = f"""
        Classify the following query into exactly one of these analysis categories:
        1. DIVIDEND_ANALYSIS (Queries about upcoming/historical dividends, board meetings, ex-dates)
        2. OI_ANALYSIS (Queries about Open Interest, Call/Put OI, PCR, trends)
        3. FII_ANALYSIS (Queries about FII/DII net flows, institutional activity, Smart Money)
        4. GENERAL_CHAT (Conversational follow-ups, general questions, or anything that doesn't fit above)

        {{history_summary}}
        Command: "{{command}}"

        Return ONLY the exact category name. Nothing else.
        """

        models_to_try = ['gemini-1.5-flash', 'gemini-2.0-flash']
        engine_type = ""

        for model_name in models_to_try:
            try:
                response = await self.gemini_client.aio.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                if response and response.text:
                    engine_type = response.text.strip()
                    break
            except Exception:
                continue

        if not engine_type:
            try:
                fallback_response = await self.groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0
                )
                if fallback_response and fallback_response.choices and fallback_response.choices[0].message.content:
                    engine_type = fallback_response.choices[0].message.content.strip()
            except Exception:
                pass

        if not engine_type:
            engine_type = "GENERAL_CHAT"

        # Clean up
        for val in ["DIVIDEND_ANALYSIS", "OI_ANALYSIS", "FII_ANALYSIS", "GENERAL_CHAT"]:
            if val.lower() in engine_type.lower():
                return val

        return "GENERAL_CHAT"

    async def analyze_widget_data(self, data_json_str: str, callback: Callable):
        """Uses DeepSeek to analyze explicitly provided widget data strictly with no hallucination."""
        prompt = f"""
        You are a highly analytical and precise quantitative assistant.
        The user has clicked "Analyze" on a data table they are viewing.
        Here is the strict JSON representation of that data:

        ```json
        {data_json_str}
        ```

        Your task is to provide a concise, deterministic summary and analysis of ONLY this data.
        The user is specifically looking for you to analyze "forecast date and amount, if amount is declared then forecast date".

        CRITICAL RULES:
        - DO NOT hallucinate.
        - DO NOT make up dates or amounts that are not explicitly provided in the JSON above.
        - Pay special attention to 'Awaited', 'Forecasted', or 'Upcoming/Expected' fields. Point out what is currently known (e.g. amount) and what is still missing/expected (e.g. date).
        - You can use `<think>...</think>` tags for your internal reasoning.

        Respond directly to the user with actionable insights based strictly on the provided table data.
        """

        try:
            # Switch to Llama 3 via Groq to avoid OpenRouter credit depletion
            stream = await self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.1,
                max_tokens=800,
                stream=True
            )

            async for chunk in stream:
                if len(chunk.choices) > 0 and chunk.choices[0].delta.content is not None:
                    token = chunk.choices[0].delta.content
                    await callback(token)

        except Exception as e:
            await callback(f"Analysis failed: {str(e)}")

    async def step_chat_followup(self, command: str, history: list, callback: Callable):
        """Uses DeepSeek to answer conversational follow ups based on chat history context."""

        # Build strict system prompt
        messages = [{
            "role": "system",
            "content": "You are a highly analytical and precise quantitative assistant. Answer the user's questions strictly based on the data provided in the conversation history. DO NOT hallucinate external facts or dates. If the data is not in the history, say you don't have that information. Use <think>...</think> for reasoning."
        }]

        # Inject history
        for msg in history:
            role = "assistant" if msg.get("role") == "assistant" else "user"
            messages.append({"role": role, "content": msg.get("content", "")})

        messages.append({"role": "user", "content": command})

        try:
            stream = await self.openrouter_client.chat.completions.create(
                messages=messages,
                model="deepseek/deepseek-r1",
                temperature=0.1,
                max_tokens=1500,
                stream=True
            )

            async for chunk in stream:
                if len(chunk.choices) > 0 and chunk.choices[0].delta.content is not None:
                    token = chunk.choices[0].delta.content
                    await callback(token)

        except Exception as e:
            await callback(f"Follow up failed: {str(e)}")

    async def step2_extract_parameters(self, command: str) -> dict:
        """Uses Llama/Groq to extract basic parameters (like stock symbol) for data queries."""
        import json
        prompt = f"""
        You are a Data Parameters Extractor. Extract the official NSE symbol if mentioned in the text.
        Use the `search_db_symbol` tool if a company name is used instead of a ticker.

        Command: "{command}"

        Output your reasoning in <reasoning> tags, then a strict JSON object:
        {{
            "symbols": ["RELIANCE"] // Official NSE ticker, or empty if none
        }}
        """
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_db_symbol",
                    "description": "Searches for an official NSE symbol based on a company name.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"}
                        },
                        "required": ["query"]
                    }
                }
            }
        ]

        try:
            response = await self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                tools=tools,
                tool_choice="auto"
            )

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if tool_calls:
                for tool_call in tool_calls:
                    if tool_call.function.name == "search_db_symbol":
                        args = json.loads(tool_call.function.arguments)
                        q = args.get("query", "")
                        symbol_result = search_db_symbol(q, self.db)
                        if symbol_result:
                            return {"symbols": [symbol_result]}

            raw_text = response_message.content or ""
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if match:
                res = json.loads(match.group(0))
                return res
            return {"symbols": []}
        except Exception:
            return {"symbols": []}

    async def run_deterministic_analysis(self, intent: str, params: dict, command: str, history: list, callback) -> None:
        """Fetches deterministic DB data and streams DeepSeek analysis."""
        import json
        data_context = {}
        symbols = params.get("symbols", [])

        if intent == "DIVIDEND_ANALYSIS":
            from backend.web.api.data.special_sit_routes import get_special_sit_dividends
            div_data = get_special_sit_dividends(db=self.db)
            if symbols and "data" in div_data:
                filtered = [d for d in div_data["data"] if d.get("symbol") in symbols]
                data_context["dividend_data"] = {"eq_date": div_data.get("eq_date"), "data": filtered}
            else:
                data_context["dividend_data"] = div_data

        elif intent == "OI_ANALYSIS":
            if symbols:
                from backend.web.api.data.derivatives_routes import get_oi_analysis
                oi_data = get_oi_analysis(symbol=symbols[0], db=self.db)
                data_context["options_data"] = oi_data
            else:
                data_context["options_data"] = "Please specify a symbol for OI Analysis."

        elif intent == "FII_ANALYSIS":
            from backend.web.api.analysis_routes import get_fii_stats_money
            fii_data = get_fii_stats_money(days=30, db=self.db)
            data_context["fii_data"] = fii_data

        history_text = ""
        for msg in history[-3:]:
            history_text += f"{msg.get('role', 'unknown').capitalize()}: {msg.get('content', '')}\n"

        prompt = f"""
        You are an expert quantitative trading analyst named Jules.
        Your sole task is to answer the user's question with absolute accuracy, using ONLY the data provided below.

        CRITICAL RULES:
        1. DO NOT HALLUCINATE dates, numbers, or events.
        2. If the user asks about something not present in the Provided Data JSON, explicitly state: "I don't have that data in my current context."
        3. Explain your internal reasoning thoroughly inside `<think>...</think>` tags before writing the final response.
        4. Keep the final text output clean, professional, and actionable. Do not dump raw JSON. Format lists nicely.

        Intent Type: {intent}
        Detected Symbols: {symbols}

        Provided Data JSON (deterministic from backend):
        {json.dumps(data_context, default=str)}

        Recent Conversation Context:
        {history_text}

        User Query: "{command}"
        """

        try:
            # Switch to Llama 3 via Groq to avoid OpenRouter credit depletion
            stream = await self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.1,
                max_tokens=800,
                stream=True
            )

            async for chunk in stream:
                if len(chunk.choices) > 0 and chunk.choices[0].delta.content is not None:
                    token = chunk.choices[0].delta.content
                    await callback(token)

        except Exception as e:
            await callback(f"\n[Analysis failed: {str(e)}]")

    async def step2_data_clerk_retrieval(self, command: str) -> Dict[str, Any]:
        """Uses Qwen to parse a data retrieval command and output a direct Widget JSON payload."""
        prompt = f"""
        You are a Data Extraction Clerk. The user wants to retrieve data, not execute a trade.
        Your job is to parse the user's intent and return a structured JSON Widget configuration.

        Command: "{command}"

        You MUST heavily utilize the `search_db_symbol` tool to map any natural language company names (like "Reliance" or "HDFC") to their exact, official NSE ticker symbol (e.g., "RELIANCE", "HDFCBANK"). Do not guess the ticker, ALWAYS verify it if it's a company name rather than a raw ticker string.

        Extract the following if present:
        - "symbols": Array of OFFICIAL NSE stock symbols. Ensure you have mapped company names to these symbols using the tool. If none mentioned or applicable (e.g. general market query), return empty array.
        - "months": Array of full month names (e.g. "July") if the user specifies a timeframe, month, or season.
        - "upcoming": Boolean, true if the user asks for upcoming events, future dates, or if they do NOT explicitly ask for "historical" data. If they just say "opportunities" or "meetings", assume upcoming=true.

        If the user asks a follow-up question (e.g. "show historical data also for july"), ensure you properly combine their intent to adjust the `upcoming` flag and `months`.

        Then, output your reasoning inside `<reasoning>` tags.
        After the reasoning, output a STRICT JSON object representing the widget payload.
        It MUST contain:
        {{
            "widget": "dividend_table",
            "symbols": [],
            "months": [],
            "upcoming": false,
            "summary": ""
        }}
        Leave summary empty. Do NOT write conversational text.

        Output the JSON block clearly at the end.
        """

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_db_symbol",
                    "description": "Searches the local Historical Data database for a matching official NSE symbol based on a company name.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The company name to search for."
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]

        messages = [{"role": "user", "content": prompt}]
        qwen_reasoning = ""
        widget_json_str = ""

        try:
            for _ in range(3):  # Max tool calls
                response = await self.openrouter_client.chat.completions.create(
                    model="qwen/qwen3-32b",
                    messages=messages,
                    tools=tools,
                    temperature=0.0,
                    max_tokens=1500
                )
                message = response.choices[0].message
                messages.append(message)

                if message.tool_calls:
                    from fastapi.concurrency import run_in_threadpool
                    for tool_call in message.tool_calls:
                        if tool_call.function.name == "search_db_symbol":
                            args = json.loads(tool_call.function.arguments)
                            res = await run_in_threadpool(search_db_symbol, self.db, args.get("query", ""))
                            messages.append({
                                "role": "tool",
                                "name": "search_db_symbol",
                                "content": str(res),
                                "tool_call_id": tool_call.id
                            })
                    continue

                raw_text = message.content.strip() if message.content else ""

                res_match = re.search(r'<reasoning>(.*?)</reasoning>', raw_text, re.DOTALL | re.IGNORECASE)
                if res_match:
                    qwen_reasoning += res_match.group(1).strip()

                # Extract JSON block
                # Using [\s\S]* to match across newlines without removing them, preserving valid JSON
                json_match = re.search(r'(\{[\s\S]*\})', raw_text)
                if json_match:
                    widget_json_str = json_match.group(1)
                else:
                    # Fallback cleanup
                    clean_text = re.sub(r'<reasoning>[\s\S]*?</reasoning>', '', raw_text, flags=re.IGNORECASE).strip()
                    # Strip out any markdown formatting
                    clean_text = re.sub(r'```json\s*', '', clean_text)
                    clean_text = re.sub(r'```\s*', '', clean_text)
                    if clean_text.startswith('{'):
                        widget_json_str = clean_text

                break

            if widget_json_str:
                widget_data = json.loads(widget_json_str)
                widget_data['qwen_reasoning'] = qwen_reasoning
                return widget_data
            else:
                return {"widget": "error", "summary": "Failed to parse data parameters."}

        except Exception as e:
            return {"widget": "error", "summary": f"Extraction error: {str(e)}"}

    async def step2_data_clerk(self, command: str, engine_type: str) -> Dict[str, Any]:
        """Uses Qwen 2.5 (OpenRouter) to extract ticker and fetch real data."""
        # 1. Extract Ticker
        prompt = f"""
        Extract the official NSE stock ticker symbol from this command.
        You must use deep logical deliberate reasoning and chain of thought (think through a feedback loop internally) before answering.

        Critically, you must resolve common Indian market terms into their exact official NSE database tickers (e.g., NIFTY, BANKNIFTY).
        Do NOT output Yahoo Finance specific tickers like 'NSEI' or '^NSEI' in the final output. The downstream system requires the official Indian exchange ticker.

        You have several tools at your disposal:
        1. `search_db_symbol`: Use this FIRST to accurately identify the official NSE ticker symbol from the local database if a company name or vague entity is mentioned.
        2. `fetch_detailed_db_data`: Once you have the exact official ticker, you MUST call this to extract deeper contextual data (historical prices, volatility, P/E, corporate actions) from our local app database to aid the downstream quantitative models.
        3. `search_yfinance_symbol` / `fetch_yfinance_historical`: Use these only as a last resort if the local database yields no results.

        Output your logic first inside `<reasoning>` tags.
        If no ticker is found, return "NONE" in the ticker tag.
        Command: "{command}"

        After your reasoning and all tool calls are complete, your final output MUST contain the final official NSE ticker string in uppercase (or NONE) enclosed in `<ticker>` tags, for example `<ticker>NIFTY</ticker>`.
        """

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_db_symbol",
                    "description": "Searches the local Historical Data database (Security Master & Bhavcopy) for a matching official NSE symbol based on a company name or partial query. Always try this first.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The company name or partial symbol to search for."
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_yfinance_symbol",
                    "description": "Searches Yahoo Finance for a matching ticker symbol based on a company name. Very useful if the local DB search fails.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The company name or entity to search for on Yahoo Finance."
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "fetch_detailed_db_data",
                    "description": "Fetches deep context from the local DB, including historical prices, open interest, P/E, volatility, and corporate actions. Always call this once you know the exact ticker.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ticker": {
                                "type": "string",
                                "description": "The exact official NSE ticker symbol (e.g., RELIANCE)."
                            },
                            "days": {
                                "type": "integer",
                                "description": "Number of days of historical data to retrieve (default: 30)."
                            }
                        },
                        "required": ["ticker"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "fetch_yfinance_historical",
                    "description": "Fetches historical price trends and recent news from Yahoo Finance. Useful for getting broader internet context.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ticker": {
                                "type": "string",
                                "description": "The exact official NSE ticker symbol."
                            },
                            "days": {
                                "type": "integer",
                                "description": "Number of days of historical data to retrieve (default: 30)."
                            }
                        },
                        "required": ["ticker"]
                    }
                }
            }
        ]

        qwen_reasoning = ""
        messages = [{"role": "user", "content": prompt}]
        max_tool_calls = 5 # Increased due to additional tools
        current_calls = 0
        ticker = "NONE"
        deep_data_cache = {}

        while current_calls < max_tool_calls:
            try:
                response = await self.openrouter_client.chat.completions.create(
                    model="qwen/qwen3-32b",
                    messages=messages,
                    tools=tools,
                    temperature=0.0,
                    max_tokens=1500
                )

                message = response.choices[0].message
                messages.append(message)

                # Check for tool calls
                if message.tool_calls:
                    from fastapi.concurrency import run_in_threadpool
                    for tool_call in message.tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)

                        tool_result = "Tool execution failed."
                        if function_name == "search_db_symbol":
                            tool_result = await run_in_threadpool(search_db_symbol, self.db, function_args.get("query", ""))
                        elif function_name == "search_yfinance_symbol":
                            tool_result = await run_in_threadpool(search_yfinance_symbol, function_args.get("query", ""))
                        elif function_name == "fetch_detailed_db_data":
                            tool_result = await run_in_threadpool(fetch_detailed_db_data, self.db, function_args.get("ticker", ""), function_args.get("days", 30))
                            deep_data_cache["local_db_deep_dive"] = json.loads(tool_result) if tool_result.startswith("{") else tool_result
                        elif function_name == "fetch_yfinance_historical":
                            tool_result = await run_in_threadpool(fetch_yfinance_historical, function_args.get("ticker", ""), function_args.get("days", 30))
                            deep_data_cache["yfinance_deep_dive"] = json.loads(tool_result) if tool_result.startswith("{") else tool_result

                        # For OpenRouter compatibility, `content` must be a string.
                        messages.append({
                            "role": "tool",
                            "name": function_name,
                            "content": str(tool_result),
                            "tool_call_id": tool_call.id
                        })
                    current_calls += 1
                    continue # Loop back to get Qwen's response to the tool output

                # Process final textual output
                raw_text = message.content.strip() if message.content else ""

                # Extract reasoning
                reasoning_match = re.search(r'<reasoning>(.*?)</reasoning>', raw_text, re.DOTALL | re.IGNORECASE)
                if reasoning_match:
                    # Append instead of overwrite to capture reasoning across tool calls
                    qwen_reasoning += "\n" + reasoning_match.group(1).strip()

                # Extract ticker
                ticker_match = re.search(r'<ticker>(.*?)</ticker>', raw_text, re.DOTALL | re.IGNORECASE)
                if ticker_match:
                    ticker = ticker_match.group(1).strip().upper()
                    # Clean ticker
                    ticker = re.sub(r'[^A-Z0-9-]', '', ticker)
                else:
                    # Fallback if no <ticker> tags are found
                    raw_text_no_reasoning = re.sub(r'<reasoning>.*?</reasoning>', '', raw_text, flags=re.DOTALL | re.IGNORECASE).strip()
                    ticker = raw_text_no_reasoning.upper()
                    ticker = re.sub(r'[^A-Z0-9-]', '', ticker)

                if not ticker: ticker = "NONE"
                break # We got a final text answer without tool calls

            except Exception as e:
                ticker = "NONE"
                qwen_reasoning += f"\n[Error querying Qwen: {e}]"
                break

        # 2. Fetch Real Data (Zero Hallucination)
        from fastapi.concurrency import run_in_threadpool
        real_data = await run_in_threadpool(fetch_bhavcopy_data, self.db, ticker)
        real_data['qwen_reasoning'] = qwen_reasoning.strip()

        # Merge any deep data fetched by Qwen into the final real_data matrix
        if "local_db_deep_dive" in deep_data_cache:
            real_data['local_db_history'] = deep_data_cache["local_db_deep_dive"]
        if "yfinance_deep_dive" in deep_data_cache:
            real_data['yfinance_history'] = deep_data_cache["yfinance_deep_dive"]

        return real_data

    async def step3_quant_logic(self, command: str, engine_type: str, data_matrix: Dict[str, Any], system_constraint: str, callback: Callable) -> tuple[str, Dict[str, Any]]:
        """Uses DeepSeek to stream reasoning logic AND generate the execution numbers."""

        constraint_block = f"\nCRITICAL GOVERNANCE FEEDBACK TO FIX: {system_constraint}\n" if system_constraint else ""

        prompt = f"""
        You are a Quantitative Trading Logic Engine analyzing a {engine_type} event.
        Command: {command}

        REAL MARKET DATA (DO NOT HALLUCINATE OUTSIDE OF THIS):
        {json.dumps(data_matrix, indent=2)}
        {constraint_block}

        CRITICAL INSTRUCTIONS:
        1. You MUST use deep logical deliberate reasoning and chain of thought (think through a feedback loop internally).
        2. First, output your internal reasoning explicitly inside `<think>` ... `</think>` tags.
        3. Analyze the broader market implications, directional sentiment, and use the provided REAL MARKET DATA to calculate realistic trading targets.
        4. AFTER the `</think>` tag, you MUST output a STRICT JSON object representing the Execution Card. It must contain exactly these keys:
           - "action": string (MUST be strictly one of: "BUY", "SELL", or "HOLD")
           - "target": float (the numerical price target)
           - "stop_loss": float (the numerical stop loss)
           - "confidence": integer (0 to 100 representing confidence score)
           - "rationale": array of strings (4 to 5 step-by-step logic notes)

        The final output MUST contain this valid JSON block after the reasoning. Do not include markdown formatting like ```json around the block if possible, just the raw JSON.
        """

        try:
            stream = await self.openrouter_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="deepseek/deepseek-r1",
                temperature=0.3,
                max_tokens=1500,
                stream=True
            )

            full_text = ""
            async for chunk in stream:
                if len(chunk.choices) > 0 and chunk.choices[0].delta.content is not None:
                    token = chunk.choices[0].delta.content
                    full_text += token
                    await callback(token)

            # Parse JSON out of full_text
            json_str = full_text
            match = re.search(r'\{.*\}', full_text, re.DOTALL)
            if match:
                json_str = match.group(0)

            try:
                exec_card = json.loads(json_str)
            except Exception as e:
                exec_card = {
                    "action": "ERROR SYNTHESIZING",
                    "target": 0.0,
                    "stop_loss": 0.0,
                    "confidence": 0,
                    "rationale": ["Failed to parse DeepSeek JSON.", str(e)]
                }

            return full_text, exec_card

        except Exception as e:
            # Fallback to openai/gpt-oss-120b on OpenRouter if deepseek-r1 fails
            await callback(f"\n[DeepSeek-R1 failed: {e}. Falling back to openai/gpt-oss-120b via OpenRouter...]\n")

            stream = await self.openrouter_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="openai/gpt-oss-120b",
                temperature=0.3,
                max_tokens=1500,
                stream=True
            )

            full_text = ""
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    token = chunk.choices[0].delta.content
                    full_text += token
                    await callback(token)

            json_str = full_text
            match = re.search(r'\{.*\}', full_text, re.DOTALL)
            if match:
                json_str = match.group(0)

            try:
                exec_card = json.loads(json_str)
            except Exception as e:
                exec_card = {
                    "action": "ERROR SYNTHESIZING",
                    "target": 0.0,
                    "stop_loss": 0.0,
                    "confidence": 0,
                    "rationale": ["Failed to parse GPT-120B JSON.", str(e)]
                }

            return full_text, exec_card

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
        except Exception:
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
                model="openai/gpt-oss-120b",
                temperature=0.0,
                extra_headers={
                    "X-Zero-Retention": "true"
                }
            )
            raw_text = response.choices[0].message.content.strip()
        except Exception as e:
            return {"status": "FAIL", "critique": f"Compliance Judge encountered an error communicating with Groq: {str(e)}"}

        try:
            # Extract reasoning
            judge_reasoning = ""
            reasoning_match = re.search(r'<reasoning>(.*?)</reasoning>', raw_text, re.DOTALL | re.IGNORECASE)
            if reasoning_match:
                judge_reasoning = reasoning_match.group(1).strip()

            match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if match:
                text = match.group(0)
            else:
                text = raw_text

            judge_res = json.loads(text)
            judge_res['reasoning'] = judge_reasoning
            return judge_res
        except Exception as e:
            # If the judge fails to parse or respond, we fail safely to trigger a retry
            return {"status": "FAIL", "critique": f"Compliance Judge encountered a parsing error checking output: {str(e)}"}

    async def step6_persona_filter(self, exec_card: Dict[str, Any]) -> Dict[str, Any]:
        """Uses Gemini to rewrite the execution card into a Quant Desk tone."""
        prompt = f"""
        You are 'Jules', the Head Strategist for a Hedge Fund.
        The Quant Engine and Governance Judge have finalized the trading numbers.
        Your job is to summarize and rewrite the following trading execution output to have a professional, highly concise 'Quant Desk' tone.
        Remove wordy, robotic phrases. Ensure the formatting is actionable, highlighting the critical signal.

        Original Input:
        {json.dumps(exec_card, indent=2)}

        You MUST use deep logical deliberate reasoning and chain of thought (think through a feedback loop internally) to determine the best phrasing.
        You can output your internal thought process inside `<reasoning>` tags.
        Then, return a strict JSON object with the exact same keys:
        - "action": string (MUST be strictly one of: "BUY", "SELL", or "HOLD")
        - "target": float
        - "stop_loss": float
        - "confidence": integer
        - "rationale": array of strings (Rewrite the 4 to 5 strong logical reasons to be short, sharp quant desk notes/bullet points summarizing the logic).

        Your final output MUST contain this valid JSON block.
        """

        models_to_try = ['gemini-1.5-flash', 'gemini-2.0-flash']
        text = ""
        error_msg = ""

        for model_name in models_to_try:
            try:
                response = await self.gemini_client.aio.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                text = response.text
                break
            except Exception as e:
                error_msg = str(e)
                continue

        if not text:
            # Fallback to Llama 3
            try:
                fallback_response = await self.groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                if fallback_response and fallback_response.choices and fallback_response.choices[0].message.content:
                    text = fallback_response.choices[0].message.content.strip()
            except Exception as e:
                exec_card['reasoning'] = f"Gemini rewrite failed ({error_msg}) AND Llama 3 fallback failed ({str(e)}). Proceeding with original strategist output."
                return exec_card

        gemini_reasoning = ""
        reasoning_match = re.search(r'<reasoning>(.*?)</reasoning>', text, re.DOTALL | re.IGNORECASE)
        if reasoning_match:
            gemini_reasoning = reasoning_match.group(1).strip()

        try:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                text = match.group(0)
            final_card = json.loads(text)
            final_card['reasoning'] = gemini_reasoning
            return final_card
        except Exception as e:
            # If formatting fails, just return the original card so we don't break the UI
            exec_card['reasoning'] = gemini_reasoning + f"\n[JSON Parse Error: {str(e)}]"
            return exec_card
