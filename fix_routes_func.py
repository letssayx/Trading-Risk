with open("backend/web/api/data/view_routes.py", "r") as f:
    content = f.read()

import re

# Insert 'from sqlalchemy import func' at the top
content = re.sub(
    r"from sqlalchemy import desc, asc, or_",
    r"from sqlalchemy import desc, asc, or_, func",
    content
)

with open("backend/web/api/data/view_routes.py", "w") as f:
    f.write(content)
