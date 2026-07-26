with open('backend/ingest/tasks.py', 'r') as f:
    content = f.read()

# Remove blank lines left from replacement
import re
content = re.sub(r'\n\s*\n\s*\n\s*# Also pull forward agm_date', r'\n                            # Also pull forward agm_date', content)

with open('backend/ingest/tasks.py', 'w') as f:
    f.write(content)
