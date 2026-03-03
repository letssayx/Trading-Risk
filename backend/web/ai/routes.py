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

                # Step 1: Dispatch
                await websocket.send_json({"type": "status", "message": "Classifying command..."})
                engine_type = await orchestrator.step1_dispatch(command)
                await websocket.send_json({"type": "engine_type", "data": engine_type})

                # Setup streaming callback for Step 3
                async def stream_callback(token: str):
                    await websocket.send_json({"type": "quant_logic", "token": token})

                # Step 2 & 3 in parallel
                await websocket.send_json({"type": "status", "message": "Triggering Quant Engine & Data Matrix..."})

                task_data = asyncio.create_task(orchestrator.step2_data_clerk(command, engine_type))
                task_logic = asyncio.create_task(orchestrator.step3_quant_logic(command, engine_type, stream_callback))

                data_matrix, reasoning = await asyncio.gather(task_data, task_logic)

                # Send Data Matrix to UI
                await websocket.send_json({"type": "data_matrix", "data": data_matrix})

                # Step 4: Synthesize
                await websocket.send_json({"type": "status", "message": "Synthesizing Execution Plan..."})
                exec_card = await orchestrator.step4_strategist(command, engine_type, data_matrix, reasoning)

                # Send final execution card
                await websocket.send_json({"type": "execution", "data": exec_card})
                await websocket.send_json({"type": "done"})

            except Exception as e:
                await websocket.send_json({"type": "error", "message": f"Orchestrator Error: {str(e)}"})

    except WebSocketDisconnect:
        pass # Client disconnected
