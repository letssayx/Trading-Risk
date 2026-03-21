with open("backend/web/api/data/view_routes.py", "r") as f:
    content = f.read()

import re

# Insert 'latest: bool = Query(False),' just to make sure it's valid
content = re.sub(
    r"latest: Optional\[bool\] = False,",
    r"latest: bool = Query(False),",
    content
)

with open("backend/web/api/data/view_routes.py", "w") as f:
    f.write(content)
