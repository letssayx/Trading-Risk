with open('backend/ingest/nse_lib.py', 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "                            import re" in line:
        continue
    new_lines.append(line)

with open('backend/ingest/nse_lib.py', 'w') as f:
    f.writelines(new_lines)
print("Removed inner import re")
