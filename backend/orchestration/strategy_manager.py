import json
from sqlalchemy.orm import Session
from backend.strategies.models import Strategy
from backend.orchestration.gemini_orchestrator import GeminiOrchestrator
import uuid

def save_natural_language_strategy(
    db: Session,
    user_id: str,
    strategy_name: str,
    user_input: str
) -> Strategy:
    """
    1. Sends user_input to Gemini to get JSON config + Python code.
    2. Validates the code (mock).
    3. Saves the record to the PostgreSQL registry.
    """

    # 1. AI Translation
    orchestrator = GeminiOrchestrator()
    ai_output = orchestrator.translate_to_logic(user_input)

    # 2. Validation (Mock compile check)
    try:
        compile(ai_output['python_code'], '<string>', 'exec')
    except SyntaxError as e:
        raise ValueError(f"AI generated invalid Python code: {e}")

    # 3. Persistence
    # Note: user_id input is string, model expects UUID. Convert if needed.
    # For now assuming user_id passed is a valid UUID string.

    new_strategy = Strategy(
        user_id=user_id, # SQLAlchemy/Postgres handles string-to-uuid if configured or passed as uuid obj
        name=strategy_name,
        config_json=ai_output['config'],
        source_code=ai_output['python_code'],
        version=1
    )

    db.add(new_strategy)
    db.commit()
    db.refresh(new_strategy)

    return new_strategy
