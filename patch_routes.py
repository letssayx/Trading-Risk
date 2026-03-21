import re

with open('backend/web/api/data/view_routes.py', 'r') as f:
    code = f.read()

# I want to find the exact place the 500 error happens. Wait, I can't start the DB.
# Let's inspect the `process_results` or the query filtering for `dividend`.
