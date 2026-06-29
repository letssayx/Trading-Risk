import json
import re
from typing import Dict, Any, Callable
from sqlalchemy.orm import Session
from sqlalchemy import text
from groq import AsyncGroq
from google import genai
from openai import AsyncOpenAI  # Used for OpenRouter
from backend.web.ai.tools import fetch_bhavcopy_data, search_db_symbol, fetch_detailed_db_data, fetch_yfinance_historical
from backend.web.ai.models import Skill, SkillStep, SkillKnowledge, SkillExample, VeteranAnnotation, ReportChunk, TradeReasoning
from backend.web.ai.embedding import get_bge_m3_embedding

# Workspace to skill group mapping
WORKSPACE_SKILLS = {
  "DERIVATIVES":       ["oi_analysis", "rollover_analysis", "expiry_behaviour", "options_analysis", "mwpl_analysis", "strategy_analysis"],
  "FUNDAMENTAL":       ["pe_analysis", "peer_comparison", "earnings_analysis"],
  "TECHNICAL":         ["technical_analysis", "fibonacci_analysis", "historical_volatility", "beta_rsquared"],
  "RISK":              ["risk_analysis", "black_swan", "historical_volatility"],
  "MACRO":             ["macro_analysis", "sectoral_analysis", "commodity_analysis", "thematic_analysis"],
  "COMMODITY":         ["commodity_analysis", "commodity_technical", "commodity_fundamental", "commodity_macro"],
  "SPECIAL_SITUATION": ["special_situation", "corporate_action", "corporate_research"],
  "EARNINGS":          ["earnings_analysis", "pe_analysis"],
  "BLACK_SWAN":        ["black_swan", "risk_analysis"],
}

class TerminalOrchestrator:
    def __init__(self, groq_key: str, openrouter_key: str, db: Session, session_id: str):
        self.groq_client = AsyncGroq(api_key=groq_key) if groq_key else None
        self.openrouter_client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key,
        ) if openrouter_key else None
        self.db = db
        self.session_id = session_id

    async def step1_detect_skill_and_symbols(self, command: str, workspace: str) -> tuple[str, list]:
        """Detects the required skill from groq, and ALSO extracts any stock symbols mentioned."""
        import json
        prompt = f"""
        You are a financial router.
        User query: "{command}"
        Current Workspace: "{workspace}"

        Available Skills for {workspace}: {", ".join(WORKSPACE_SKILLS.get(workspace, []))}

        1. Select the BEST matching skill. If none fits perfectly, pick the most generic one for the workspace.
        2. Extract any Indian stock ticker symbols mentioned in the query (e.g. NIFTY, BANKNIFTY, RELIANCE).

        Return exactly and only a JSON object like:
        {{"skill_id": "oi_analysis", "symbols": ["NIFTY", "RELIANCE"]}}
        """

        try:
            response = await self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.1
            )
            raw_text = response.choices[0].message.content.strip()
            # Clean possible markdown JSON fences
            if raw_text.startswith("```json"):
                raw_text = raw_text.replace("```json", "").replace("```", "").strip()

            data = json.loads(raw_text)
            skill_id = data.get("skill_id", WORKSPACE_SKILLS.get(workspace, ["technical_analysis"])[0])
            symbols = data.get("symbols", [])
            return skill_id, symbols
        except Exception as e:
            print(f"Skill/Symbol routing failed: {e}")
            default_skill = WORKSPACE_SKILLS.get(workspace, ["technical_analysis"])[0]
            return default_skill, []

    async def step1_detect_skill(self, command: str, workspace: str) -> str:
        """Micro-routing: Ask Groq to pick the best skill in the workspace for the given query."""
        if not workspace or workspace not in WORKSPACE_SKILLS:
            workspace = "DERIVATIVES" # Fallback

        allowed_skills = WORKSPACE_SKILLS[workspace]
        prompt = f"""
        Given the following user query and a strict list of allowed skills for the current workspace ({workspace}),
        return ONLY the exact string ID of the skill that best fits the query. Do not return anything else.

        Allowed Skills: {', '.join(allowed_skills)}

        User Query: "{command}"
        """

        try:
            if self.groq_client:
                response = await self.groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0
                )
                skill_id = response.choices[0].message.content.strip().lower()
                # Clean up any quotes or markdown
                skill_id = re.sub(r'[^a-z_]', '', skill_id)
                if skill_id in allowed_skills:
                    return skill_id
        except Exception as e:
            print(f"Skill router error: {e}")

        # Fallback to first skill if error
        return allowed_skills[0]

    def step2_pull_skill_package(self, skill_id: str, query_embedding: list):
        # 1. Pull Steps
        steps_objs = self.db.query(SkillStep).filter(SkillStep.skill_id == skill_id).order_by(SkillStep.step_number).all()
        steps = [f"Step {s.step_number}: {s.step_content}" for s in steps_objs]
        embedding_str = str(query_embedding).replace(' ', '')

        # We use a raw SQL for vector similarity because SQLAlchemy pgvector integration
        # can sometimes be finicky depending on the connection driver.
        # This executes: SELECT content FROM skill_knowledge ORDER BY embedding <=> '[...]' LIMIT 5;

        # 2. Pull Knowledge (Top 5)
        knowledge = []
        try:
            k_sql = text("""
                SELECT content, title FROM skill_knowledge
                WHERE skill_id = :skill_id AND embedding IS NOT NULL
                ORDER BY embedding <=> :emb::vector LIMIT 5
            """)
            k_res = self.db.execute(k_sql, {"skill_id": skill_id, "emb": embedding_str}).fetchall()
            knowledge = [f"[{r[1]}]: {r[0]}" for r in k_res]
        except Exception as e:
            print(f"Error fetching knowledge vectors: {e}")

        # 3. Pull Examples (Top 3)
        examples = []
        try:
            e_sql = text("""
                SELECT think_chain, answer FROM skill_examples
                WHERE skill_id = :skill_id AND embedding IS NOT NULL
                ORDER BY embedding <=> :emb::vector LIMIT 3
            """)
            e_res = self.db.execute(e_sql, {"skill_id": skill_id, "emb": embedding_str}).fetchall()
            examples = [{"think": r[0], "answer": r[1]} for r in e_res]
        except Exception as e:
            print(f"Error fetching example vectors: {e}")

        return steps, knowledge, examples

    def step3_pull_rag_context(self, query_embedding: list, skill_id: str):
        embedding_str = str(query_embedding).replace(' ', '')

        veteran_annotations = []
        report_chunks = []
        past_trades = []

        try:
            v_sql = text("""
                SELECT annotation_text FROM veteran_annotations
                WHERE skill_id = :skill_id AND embedding IS NOT NULL
                ORDER BY embedding <=> :emb::vector LIMIT 3
            """)
            v_res = self.db.execute(v_sql, {"skill_id": skill_id, "emb": embedding_str}).fetchall()
            veteran_annotations = [r[0] for r in v_res]

            r_sql = text("""
                SELECT chunk_text FROM report_chunks
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> :emb::vector LIMIT 3
            """)
            r_res = self.db.execute(r_sql, {"emb": embedding_str}).fetchall()
            report_chunks = [r[0] for r in r_res]

            t_sql = text("""
                SELECT query, final_answer, correction FROM trade_reasoning
                WHERE skill_id = :skill_id AND user_rating >= 4 AND embedding IS NOT NULL
                ORDER BY embedding <=> :emb::vector LIMIT 2
            """)
            t_res = self.db.execute(t_sql, {"skill_id": skill_id, "emb": embedding_str}).fetchall()
            past_trades = [f"Past Q: {r[0]}\nPast A: {r[1]}\nCorrection: {r[2]}" for r in t_res]

        except Exception as e:
            print(f"Error fetching RAG context: {e}")

        return veteran_annotations, report_chunks, past_trades

    async def step4_pull_live_data(self, command: str, symbols: list):
        import asyncio
        # We use a simplified DB extraction here, combining the tools we already have
        data_snapshot = {}
        for sym in symbols:
            db_sym = await asyncio.to_thread(search_db_symbol, self.db, sym)
            if db_sym:
                data = await asyncio.to_thread(fetch_detailed_db_data, self.db, db_sym, days=30)
                data_snapshot[db_sym] = data
        return data_snapshot

    def step5_build_prompt(self, command: str, steps: list, knowledge: list, examples: list, rag_ctx: tuple, data: dict) -> str:
        v_annotations, r_chunks, p_trades = rag_ctx

        prompt = f"""
You are an expert quantitative trading terminal.

TASK: Answer the user's query rigorously based ONLY on the provided Context and Live Data.
You MUST output your internal reasoning in `<think> ... </think>` tags before providing the final answer.

### RULES & STEPS
{chr(10).join(steps)}

### KNOWLEDGE BASE
{chr(10).join(knowledge)}

### VETERAN ANNOTATIONS (Important memory)
{chr(10).join(v_annotations)}

### PAST SIMILAR SUCCESSFUL TRADES
{chr(10).join(p_trades)}

### REPORT CHUNKS
{chr(10).join(r_chunks)}

### LIVE TIMESCALEDB SNAPSHOT
{json.dumps(data, indent=2, default=str)}

### FEW-SHOT EXAMPLES
"""
        for i, ex in enumerate(examples):
            prompt += f"\nExample {i+1}:\n<think>{ex['think']}</think>\nAnswer: {ex['answer']}\n"

        prompt += f"""
### USER QUERY
{command}

Output <think> block first, then your final answer.
"""
        return prompt

    async def run_pipeline(self, command: str, workspace: str, symbols: list, stream_callback: Callable, think_callback: Callable) -> Dict[str, Any]:
        # 1. DETECT SKILL
        await think_callback("Detecting skill based on workspace...")
        skill_id, llm_symbols = await self.step1_detect_skill_and_symbols(command, workspace)
        if not symbols:
            symbols = llm_symbols
        await think_callback(f"Skill selected: {skill_id}")

        # 2. PULL SKILL PACKAGE
        await think_callback("Pulling skill package and embedded knowledge...")
        steps, knowledge, examples = self.step2_pull_skill_package(skill_id, command)

        # 3. PULL RAG CONTEXT
        await think_callback("Pulling RAG Context (Veteran Annotations, Reports)...")
        rag_ctx = self.step3_pull_rag_context(command, skill_id)

        # 4. PULL LIVE DATA
        await think_callback("Pulling live TimescaleDB snapshot...")
        live_data = await self.step4_pull_live_data(command, symbols)

        # 5. BUILD PROMPT
        prompt = self.step5_build_prompt(command, steps, knowledge, examples, rag_ctx, live_data)

        # 6. ROUTE TO MODEL (Using OpenRouter DeepSeek R1)
        await think_callback("Routing to Quantitative Engine (DeepSeek R1)...")

        final_answer = ""
        think_content = ""
        is_thinking = False

        try:
            if not self.openrouter_client:
                raise ValueError("OpenRouter client not configured.")

            stream = await self.openrouter_client.chat.completions.create(
                model="deepseek/deepseek-r1-distill-qwen-14b",
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )

            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta.content or ""

                    if "<think>" in delta:
                        is_thinking = True
                        delta = delta.replace("<think>", "")

                    if "</think>" in delta:
                        is_thinking = False
                        think_parts = delta.split("</think>")
                        think_content += think_parts[0]
                        await think_callback(think_parts[0])

                        ans_part = think_parts[1] if len(think_parts) > 1 else ""
                        final_answer += ans_part
                        await stream_callback(ans_part)
                        continue

                    if is_thinking:
                        think_content += delta
                        await think_callback(delta)
                    else:
                        final_answer += delta
                        await stream_callback(delta)

        except Exception as e:
            err = f"Engine Error: {e}"
            await stream_callback(err)
            final_answer = err

        # 8. SAVE TO trade_reasoning
        try:
            tr = TradeReasoning(
                skill_id=skill_id,
                query=command,
                context_used={"live_data": live_data},
                think_chain=think_content,
                final_answer=final_answer,
                embedding=query_embedding
            )
            self.db.add(tr)
            self.db.commit()
            self.db.refresh(tr)
            trade_id = tr.id
        except Exception as e:
            print(f"Save trade reasoning error: {e}")
            trade_id = None

        # 9. RETURN
        return {
            "think": think_content,
            "answer": final_answer,
            "skill_used": skill_id,
            "trade_id": trade_id
        }
