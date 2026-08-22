import re

with open("backend/ingest/tasks.py", "r") as f:
    content = f.read()

start_marker = r"        for sym in event_symbols:\n            ca_history = ca_by_symbol.get\(sym, \[\]\)"
end_marker = r"        return \"Dividend databank updated successfully!\""

with open("replacement_block.txt", "r") as f:
    replacement_block = f.read()

updated_content = re.sub(
    f"{start_marker}.*?{end_marker}",
    replacement_block.replace('\\', '\\\\'),
    content,
    flags=re.DOTALL
)

with open("backend/ingest/tasks.py", "w") as f:
    f.write(updated_content)
