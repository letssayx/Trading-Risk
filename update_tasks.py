import re

with open("backend/ingest/tasks.py", "r") as f:
    content = f.read()

start_marker = r"                # Try to find BM with STRICT type \+ amount match first\n                best_bm = None"
end_marker = r"                    bm_date_for_agm = None"

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
