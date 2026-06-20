import json
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
            history = payload.get("history", [])

            import os
            # Use frontend keys if provided, otherwise fallback to server environment variables
            groq_key = keys.get("groq") or os.getenv("GROQ_API_KEY")
            openrouter_key = keys.get("openrouter") or os.getenv("OPENROUTER_API_KEY")
            gemini_key = keys.get("google") or os.getenv("GOOGLE_API_KEY")

            if not (groq_key and openrouter_key and gemini_key):
                await websocket.send_json({
                    "type": "error",
                    "message": "Missing API keys. Please check server .env or set them in Config tab."
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

                if command.startswith("ANALYZE_WIDGET_DATA|"):
                    # Direct command from the table "Analyze" button
                    await websocket.send_json({"type": "status", "message": "Analyzing Table Data directly..."})
                    data_json_str = command.split("|", 1)[1]

                    await websocket.send_json({"type": "text_stream_start"})

                    async def stream_callback(token: str):
                        await websocket.send_json({"type": "text_stream", "token": token})

                    await orchestrator.analyze_widget_data(data_json_str, stream_callback)
                    await websocket.send_json({"type": "text_stream_end"})
                    continue

                # Step 1: Dispatch (Fast-Track Check First)
                await websocket.send_json({"type": "status", "message": "Classifying command intent..."})
                engine_type = await orchestrator.step1_dispatch(command, history)
                await websocket.send_json({"type": "engine_type", "data": engine_type})

                expanded_command = command

                # Only do Persona Prefilter (Jules Task Expansion) if it's NOT a simple data retrieval
                if "DATA_RETRIEVAL" not in engine_type:
                    await websocket.send_json({"type": "status", "message": "Converting command into Quant Task..."})
                    step0_res = await orchestrator.step0_persona_prefilter(command)
                    expanded_command = step0_res.get("task", command)

                    # Show Jules' reasoning
                    await websocket.send_json({
                        "type": "jules_task",
                        "message": expanded_command,
                        "reasoning": step0_res.get("reasoning", "")
                    })

                if "CHAT_FOLLOW_UP" in engine_type:
                    await websocket.send_json({"type": "status", "message": "Responding based on recent context..."})
                    await websocket.send_json({"type": "text_stream_start"})

                    async def stream_callback(token: str):
                        await websocket.send_json({"type": "text_stream", "token": token})

                    await orchestrator.step_chat_followup(command, history, stream_callback)
                    await websocket.send_json({"type": "text_stream_end"})
                elif "DATA_RETRIEVAL" in engine_type:
                    # New Fast-Track Pipeline for simple data lookups
                    await websocket.send_json({"type": "status", "message": "Extracting Data Search Parameters..."})
                    widget_payload = await orchestrator.step2_data_clerk_retrieval(expanded_command)

                    if widget_payload.get("qwen_reasoning"):
                        await websocket.send_json({"type": "qwen_extract", "reasoning": widget_payload.get("qwen_reasoning")})

                    # Send payload directly to chat UI to render widget
                    await websocket.send_json({"type": "result", "message": json.dumps(widget_payload)})
                    await websocket.send_json({"type": "done"})
                else:
                    # Setup streaming callback for Step 3
                    async def stream_callback(token: str):
                        await websocket.send_json({"type": "quant_logic", "token": token})

                    # Step 2: Data Clerk
                    await websocket.send_json({"type": "status", "message": "Triggering Data Matrix Extract..."})
                    data_matrix = await orchestrator.step2_data_clerk(expanded_command, engine_type)

                    # Send Data Matrix to UI
                    await websocket.send_json({"type": "data_matrix", "data": data_matrix})

                    # Step 3 & 5: Quant Engine <-> Compliance Judge Loop
                    await websocket.send_json({"type": "status", "message": "Starting Quant Engine Reasoning..."})

                    max_retries = 2
                    current_retry = 0
                    system_constraint = ""
                    final_exec_card = None
                    final_reasoning = ""

                    while current_retry <= max_retries:
                        # Quant Engine runs with possible system constraint feedback
                        reasoning, exec_card = await orchestrator.step3_quant_logic(
                            command=expanded_command,
                            engine_type=engine_type,
                            data_matrix=data_matrix,
                            system_constraint=system_constraint,
                            callback=stream_callback
                        )

                        # Step 5: Compliance Judge
                        await websocket.send_json({"type": "status", "message": "Running Compliance Judge Verification..."})
                        judge_result = await orchestrator.step5_compliance_judge(expanded_command, data_matrix, reasoning, exec_card)

                        if judge_result.get("reasoning"):
                            await websocket.send_json({"type": "governance_log", "message": f"Reasoning: {judge_result.get('reasoning')}"})

                        if judge_result.get("status") == "PASS":
                            final_exec_card = exec_card
                            final_reasoning = reasoning
                            break
                        else:
                            critique = judge_result.get("critique", "Unknown error in verification.")
                            await websocket.send_json({"type": "governance_log", "message": f"System self-correcting via Quant Logic restart: {critique}"})
                            system_constraint = critique
                            current_retry += 1

                    if not final_exec_card:
                        # If we exhausted retries, we fallback to the last generated card and send a warning
                        final_exec_card = exec_card
                        final_reasoning = reasoning
                        await websocket.send_json({"type": "governance_log", "message": "Warning: Max retries reached. Output may not be fully compliant."})

                    # Step 6: Strategist Summary (Persona Filter)
                    await websocket.send_json({"type": "status", "message": "Strategist summarizing final output..."})
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
