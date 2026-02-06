import os
from celery import Celery
from backend.config import Config

# Ensure env loaded
celery_app = Celery(
    "turtle_worker",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0")
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task
def run_simulation_task(scenario_id: str):
    """
    Example background task for heavy risk simulations.
    """
    import time
    print(f"Starting simulation for {scenario_id}...")
    time.sleep(5) # Simulate compute
    return {"status": "Complete", "scenario_id": scenario_id, "impact": "-5.2%"}
