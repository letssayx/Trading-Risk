import re

with open("backend/ingest/tasks.py", "r") as f:
    content = f.read()

# Define the start and end markers for replacement
start_marker = r"        for sym in event_symbols:\n            ca_history = ca_by_symbol.get\(sym, \[\]\)"
end_marker = r"        db.commit\(\)"

# Read the replacement block from a file
with open("replacement_block.txt", "r") as f:
    replacement_block = f.read()

# Make the replacement string safe for re.sub by escaping backslashes
replacement_block = replacement_block.replace('\\', '\\\\')

# Replace the block
updated_content = re.sub(
    f"{start_marker}.*?{end_marker}",
    replacement_block,
    content,
    flags=re.DOTALL
)

with open("backend/ingest/tasks.py", "w") as f:
    f.write(updated_content)
