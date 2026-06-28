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
            workspace = payload.get("workspace", "DERIVATIVES")
            symbols = payload.get("symbols", [])

            groq_key = keys.get("groq") or os.getenv("GROQ_API_KEY")
            openrouter_key = keys.get("openrouter") or os.getenv("OPENROUTER_API_KEY")

            orchestrator = TerminalOrchestrator(
                groq_key=groq_key,
                openrouter_key=openrouter_key,
                db=db,
                session_id=session_id
            )

            async def stream_callback(token: str):
                await websocket.send_text(json.dumps({"type": "stream", "chunk": token}))

            async def think_callback(token: str):
                await websocket.send_text(json.dumps({"type": "think", "chunk": token}))

            result = await orchestrator.run_pipeline(
                command=command,
                workspace=workspace,
                symbols=symbols,
                stream_callback=stream_callback,
                think_callback=think_callback
            )

            await websocket.send_text(json.dumps({
                "type": "final",
                "skill_used": result["skill_used"],
                "trade_id": result["trade_id"]
            }))
except WebSocketDisconnect:
        pass # Client disconnected

# ---------------------------------------------------------
# SKILL REGISTRY & RAG ENDPOINTS
# ---------------------------------------------------------
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from backend.web.ai.models import Skill, SkillStep, SkillKnowledge, SkillExample, VeteranAnnotation, ReportChunk, RegulatoryChunk, TradeReasoning
from backend.web.ai.embedding import get_bge_m3_embedding

class KnowledgeBlock(BaseModel):
    knowledge_type: str
    title: str
    content: str
    priority: int = 1

class ExampleBlock(BaseModel):
    market_context: Optional[Dict[str, Any]] = None
    think_chain: str
    answer: str
    quality_score: int = 5

class AnnotationBlock(BaseModel):
    annotation_text: str
    market_context: Optional[Dict[str, Any]] = None
    symbols: List[str] = []
    skill_id: str
    was_correct: bool = True
    outcome_notes: str = ""

@ai_router.get("/api/ai/skills")
def list_skills(db: Session = Depends(get_db)):
    skills = db.query(Skill).all()
    return [{"skill_id": s.skill_id, "name": s.name, "workspace": s.workspace, "description": s.description} for s in skills]

@ai_router.get("/api/ai/skills/{skill_id}")
def get_skill(skill_id: str, db: Session = Depends(get_db)):
    skill = db.query(Skill).filter(Skill.skill_id == skill_id).first()
    if not skill:
        return {"error": "Skill not found"}
    steps = db.query(SkillStep).filter(SkillStep.skill_id == skill_id).order_by(SkillStep.step_number).all()
    knowledge = db.query(SkillKnowledge).filter(SkillKnowledge.skill_id == skill_id).all()
    examples = db.query(SkillExample).filter(SkillExample.skill_id == skill_id).all()

    return {
        "skill": {"skill_id": skill.skill_id, "name": skill.name, "workspace": skill.workspace},
        "steps": [{"step_number": s.step_number, "title": s.step_title, "content": s.step_content} for s in steps],
        "knowledge": [{"id": k.id, "title": k.title, "content": k.content, "priority": k.priority} for k in knowledge],
        "examples": [{"id": e.id, "answer": e.answer, "quality_score": e.quality_score} for e in examples]
    }

@ai_router.put("/api/ai/skills/{skill_id}/knowledge")
def add_knowledge(skill_id: str, payload: KnowledgeBlock, db: Session = Depends(get_db)):
    # Crucial: Generate 1024-dim embedding before insert
    embedding = get_bge_m3_embedding(payload.content)

    k = SkillKnowledge(
        skill_id=skill_id,
        knowledge_type=payload.knowledge_type,
        title=payload.title,
        content=payload.content,
        priority=payload.priority,
        embedding=embedding
    )
    db.add(k)
    db.commit()
    db.refresh(k)
    return {"status": "success", "id": k.id}

@ai_router.post("/api/ai/skills/{skill_id}/examples")
def add_example(skill_id: str, payload: ExampleBlock, db: Session = Depends(get_db)):
    # Combine answer + think_chain for embedding context
    text_to_embed = f"Think: {payload.think_chain}\nAnswer: {payload.answer}"
    embedding = get_bge_m3_embedding(text_to_embed)

    e = SkillExample(
        skill_id=skill_id,
        market_context=payload.market_context,
        think_chain=payload.think_chain,
        answer=payload.answer,
        quality_score=payload.quality_score,
        embedding=embedding
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    return {"status": "success", "id": e.id}

@ai_router.get("/api/ai/skills/{skill_id}/examples")
def get_examples(skill_id: str, db: Session = Depends(get_db)):
    examples = db.query(SkillExample).filter(SkillExample.skill_id == skill_id).all()
    return [{"id": e.id, "answer": e.answer, "quality_score": e.quality_score} for e in examples]

@ai_router.post("/api/ai/rag/annotate")
def add_annotation(payload: AnnotationBlock, db: Session = Depends(get_db)):
    embedding = get_bge_m3_embedding(payload.annotation_text)
    a = VeteranAnnotation(
        annotation_text=payload.annotation_text,
        market_context=payload.market_context,
        symbols=payload.symbols,
        skill_id=payload.skill_id,
        was_correct=payload.was_correct,
        outcome_notes=payload.outcome_notes,
        embedding=embedding
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return {"status": "success", "id": a.id}

@ai_router.get("/api/ai/export-training-data")
def export_training_data(min_rating: int = 4, skill_id: str = None, db: Session = Depends(get_db)):
    query = db.query(TradeReasoning).filter(TradeReasoning.user_rating >= min_rating)
    if skill_id:
        query = query.filter(TradeReasoning.skill_id == skill_id)

    records = query.all()
    return [
        {
            "id": r.id,
            "skill_id": r.skill_id,
            "query": r.query,
            "context_used": r.context_used,
            "think_chain": r.think_chain,
            "final_answer": r.final_answer,
            "user_rating": r.user_rating,
            "correction": r.correction
        }
        for r in records
    ]

# Placeholders for PDF and Regulatory ingest endpoints
@ai_router.post("/api/ai/rag/ingest/pdf")
def ingest_pdf():
    return {"status": "Not implemented"}

@ai_router.post("/api/ai/rag/ingest/regulatory")
def ingest_regulatory():
    return {"status": "Not implemented"}

@ai_router.post("/api/ai/chat")
async def chat_endpoint(payload: dict, db: Session = Depends(get_db)):
    # Standard POST endpoint for AI Chat, mainly for programmatic access.
    # The actual UI relies heavily on the websocket /ws/ai-analyze, which we will refactor.
    return {"status": "Use WebSocket /ws/ai-analyze for streaming"}
