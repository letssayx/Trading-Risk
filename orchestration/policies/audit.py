import logging
import json
from datetime import datetime
from typing import Dict, Any

# Configure a specific logger for auditing
audit_logger = logging.getLogger("audit_trail")
audit_logger.setLevel(logging.INFO)

# In a real app, this would write to a DB or a secure file
# For now, we configure it to write to a file
handler = logging.FileHandler("audit.log")
formatter = logging.Formatter('%(asctime)s - %(message)s')
handler.setFormatter(formatter)
audit_logger.addHandler(handler)

def log_action(user_id: str, action: str, details: Dict[str, Any]):
    """
    Records an action to the audit trail.
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "action": action,
        "details": details
    }

    # Log as JSON for easy parsing
    audit_logger.info(json.dumps(entry))

    # In a real implementation, this would insert into the 'Audit_Log' table in PostgreSQL.
    # print(f"[AUDIT] User: {user_id} | Action: {action} | {details}")
