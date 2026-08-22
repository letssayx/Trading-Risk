import re

with open("backend/ingest/tasks.py", "r") as f:
    content = f.read()

# Define the start and end markers for replacement
start_marker = r"@shared_task\(bind=True, max_retries=3, acks_late=True, reject_on_worker_lost=True\)\ndef build_dividend_databank_task"
end_marker = r"        return f\"Error building dividend databank: \{str\(e\)\}\"\n    finally:\n        db.close\(\)"

# Read the replacement block from a file
with open("replacement_block.txt", "r") as f:
    replacement_block = f.read()

# Replace the block
updated_content = re.sub(
    f"{start_marker}.*?{end_marker}",
    replacement_block.replace('\\', '\\\\'),
    content,
    flags=re.DOTALL
)

with open("backend/ingest/tasks.py", "w") as f:
    f.write(updated_content)
