import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from backend.infrastructure.db import get_db
from sqlalchemy.orm import Session
from backend.web.ai.orchestrator import TerminalOrchestrator
from backend.ingest.nse_models import AIPrediction

ai_router = APIRouter()

@ai_router.get("/api/ai/accuracy")
def get_system_accuracy(session_id: str = "local_trader_01", db: Session = Depends(get_db)):
    """
    Calculates the benchmarking accuracy for the trader's session.
    A prediction is 'accurate' if the actual price is within 1% of the predicted price.
    """
    predictions = db.query(AIPrediction).filter(
        AIPrediction.session_id == session_id,
        AIPrediction.actual_price.isnot(None),
        AIPrediction.predicted_price > 0
    ).all()

    if not predictions:
        return {"accuracy": 0.0, "total": 0}

    accurate_count = 0
    for p in predictions:
        margin = abs((p.actual_price - p.predicted_price) / p.actual_price)
        if margin <= 0.01: # 1% margin of error
            accurate_count += 1

    accuracy_pct = round((accurate_count / len(predictions)) * 100, 2)
    return {"accuracy": accuracy_pct, "total": len(predictions)}

@ai_router.websocket("/ws/ai-analyze")
async def ai_analyze_ws(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()
    try:
        while True:
            # 1. Receive command and keys
            data = await websocket.receive_text()
            payload = json.loads(data)

            command = payload.get("command")
            keys = payload.get("keys", {})
            session_id = payload.get("session_id", "anonymous")

            groq_key = keys.get("groq")
            openrouter_key = keys.get("openrouter")
            gemini_key = keys.get("google")

            if not (groq_key and openrouter_key and gemini_key):
                await websocket.send_json({
                    "type": "error",
                    "message": "Missing API keys. Please set them in Config tab."
                })
                continue

            if command == "STOP":
                # Handle interrupt if needed
                continue

            try:
                orchestrator = TerminalOrchestrator(
                    groq_key=groq_key,
                    openrouter_key=openrouter_key,
                    gemini_key=gemini_key,
                    db=db,
                    session_id=session_id
                )

                # Step 0: Persona Prefilter
                await websocket.send_json({"type": "status", "message": "Jules converting command into Quant Task..."})
                step0_res = await orchestrator.step0_persona_prefilter(command)
                expanded_command = step0_res.get("task", command)

                # Show Jules' reasoning + the final task
                await websocket.send_json({
                    "type": "jules_task",
                    "message": expanded_command,
                    "reasoning": step0_res.get("reasoning", "")
                })

                # Step 1: Dispatch
                await websocket.send_json({"type": "status", "message": "Classifying command..."})
                engine_type = await orchestrator.step1_dispatch(expanded_command)
                await websocket.send_json({"type": "engine_type", "data": engine_type})

                # Setup streaming callback for Step 3
                async def stream_callback(token: str):
                    await websocket.send_json({"type": "quant_logic", "token": token})

                # Step 2 & 3 in parallel
                await websocket.send_json({"type": "status", "message": "Triggering Quant Engine & Data Matrix..."})

                task_data = asyncio.create_task(orchestrator.step2_data_clerk(expanded_command, engine_type))
                task_logic = asyncio.create_task(orchestrator.step3_quant_logic(expanded_command, engine_type, stream_callback))

                data_matrix, reasoning = await asyncio.gather(task_data, task_logic)

                # Send Data Matrix to UI
                await websocket.send_json({"type": "data_matrix", "data": data_matrix})

                # Step 4: Synthesize with Retry Loop for Compliance Judge
                await websocket.send_json({"type": "status", "message": "Synthesizing Execution Plan..."})

                max_retries = 2
                current_retry = 0
                system_constraint = ""
                final_exec_card = None

                while current_retry <= max_retries:
                    modified_reasoning = reasoning
                    if system_constraint:
                        modified_reasoning += f"\n\nSYSTEM CONSTRAINT (Correct your output based on this critique):\n{system_constraint}"

                    exec_card = await orchestrator.step4_strategist(expanded_command, engine_type, data_matrix, modified_reasoning)

                    # Step 5: Compliance Judge
                    await websocket.send_json({"type": "status", "message": "Running Compliance Judge Verification..."})
                    judge_result = await orchestrator.step5_compliance_judge(expanded_command, data_matrix, reasoning, exec_card)

                    if judge_result.get("reasoning"):
                        await websocket.send_json({"type": "governance_log", "message": f"Reasoning: {judge_result.get('reasoning')}"})

                    if judge_result.get("status") == "PASS":
                        final_exec_card = exec_card
                        break
                    else:
                        critique = judge_result.get("critique", "Unknown error in verification.")
                        await websocket.send_json({"type": "governance_log", "message": f"System self-correcting: {critique}"})
                        system_constraint = critique
                        current_retry += 1

                if not final_exec_card:
                    # If we exhausted retries, we fallback to the last generated card and send a warning
                    final_exec_card = exec_card
                    await websocket.send_json({"type": "governance_log", "message": "Warning: Max retries reached. Output may not be fully compliant."})

                # Step 6: Persona Filter
                await websocket.send_json({"type": "status", "message": "Applying Quant Desk Persona..."})
                final_card = await orchestrator.step6_persona_filter(final_exec_card)

                # Persist to DB using the final approved and formatted card
                try:
                    raw_rationale = final_card.get("rationale", [])
                    if isinstance(raw_rationale, list):
                        db_rationale = " | ".join([str(r) for r in raw_rationale])
                    else:
                        db_rationale = str(raw_rationale)

                    pred = AIPrediction(
                        session_id=session_id,
                        ticker=data_matrix.get("ticker", "NIFTY"),
                        engine_type=engine_type,
                        predicted_price=float(final_card.get("predicted_price", 0)),
                        action=final_card.get("action", ""),
                        target=float(final_card.get("target", 0)),
                        stop_loss=float(final_card.get("stop_loss", 0)),
                        confidence=int(final_card.get("confidence", 0)),
                        rationale=db_rationale
                    )
                    db.add(pred)
                    db.commit()
                except Exception as db_err:
                    print(f"Error persisting prediction: {db_err}")
                    db.rollback()

                # Send final execution card
                await websocket.send_json({"type": "execution", "data": final_card})
                await websocket.send_json({"type": "done"})

            except Exception as e:
                await websocket.send_json({"type": "error", "message": f"Orchestrator Error: {str(e)}"})

    except WebSocketDisconnect:
        pass # Client disconnected
