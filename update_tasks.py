import re

with open("backend/ingest/tasks.py", "r") as f:
    content = f.read()

start_marker = r"        for sym in event_symbols:\n            ca_history = ca_by_symbol.get\(sym, \[\]\)"
end_marker = r"            # 10\. Process unmatched BMs \(awaited dividends / AGMs\)"

with open("replacement_block.txt", "r") as f:
    replacement_block = f.read()

updated_content = re.sub(
    f"{start_marker}.*?{end_marker}",
    replacement_block.replace('\\', '\\\\') + "\n            # 10. Process unmatched BMs (awaited dividends / AGMs)",
    content,
    flags=re.DOTALL
)

# the original code used 'final_dividend_events', but the prompt uses 'final_actions'
updated_content = updated_content.replace('final_dividend_events', 'final_actions')

with open("backend/ingest/tasks.py", "w") as f:
    f.write(updated_content)
