with open("backend/main.py", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "from backend.web.api import" in line and "audit_routes" in line:
        new_lines.append(line)
        new_lines.append("from backend.web.api import macro_routes\n")
    elif "app.include_router(audit_routes.router" in line:
        new_lines.append(line)
        new_lines.append("app.include_router(macro_routes.router)\n")
    else:
        new_lines.append(line)

with open("backend/main.py", "w") as f:
    f.writelines(new_lines)
