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

                # Step 1: Dispatch
                engine_type = await orchestrator.step1_dispatch(command, history)
                await websocket.send_json({"type": "engine_type", "data": engine_type})

                if engine_type == "GENERAL_CHAT":
                    await websocket.send_json({"type": "status", "message": "Responding based on recent context..."})
                    await websocket.send_json({"type": "text_stream_start"})

                    async def chat_callback(token: str):
                        await websocket.send_json({"type": "text_stream", "token": token})

                    await orchestrator.step_chat_followup(command, history, chat_callback)
                    await websocket.send_json({"type": "text_stream_end"})
                    await websocket.send_json({"type": "done"})

                else:
                    # New Deterministic Flow
                    await websocket.send_json({"type": "status", "message": "Extracting Data Search Parameters..."})
                    params = await orchestrator.step2_extract_parameters(command)

                    if params.get("symbols"):
                        await websocket.send_json({"type": "governance_log", "message": f"Identified Symbol: {params['symbols'][0]}"})

                    await websocket.send_json({"type": "status", "message": f"Fetching deterministic DB data for {engine_type}..."})

                    await websocket.send_json({"type": "text_stream_start"})

                    async def ds_callback(token: str):
                        await websocket.send_json({"type": "text_stream", "token": token})

                    await orchestrator.run_deterministic_analysis(engine_type, params, command, history, ds_callback)

                    await websocket.send_json({"type": "text_stream_end"})
                    await websocket.send_json({"type": "done"})


            except Exception as e:
                await websocket.send_json({"type": "error", "message": f"Orchestrator Error: {str(e)}"})

    except WebSocketDisconnect:
        pass # Client disconnected
