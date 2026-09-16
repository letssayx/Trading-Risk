from celery import Celery
import os
from dotenv import load_dotenv


import time
os.environ["TZ"] = "Asia/Kolkata"
time.tzset()

# Load env variables explicitly when worker boots
load_dotenv(override=True)

# Placeholder Celery App
# In production, this would load config from backend.config
broker_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
app = Celery(
    "turtle_worker",
    broker=broker_url,
    include=['backend.ingest.tasks', 'backend.ingest.audit_tasks']
)

# Register tasks

@app.task
def run_governance_rubric(portfolio_id: str):
    print(f"Executing Governance Rubric for {portfolio_id}")
    return {"status": "COMPLETED", "score": 95}
