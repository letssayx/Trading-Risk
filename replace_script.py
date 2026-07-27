import re

with open('backend/ingest/nse_lib.py', 'r') as f:
    content = f.read()

target = """                        if has_div or has_rd or is_agm:
                            found_amount = None
                            found_record_date = None
                            found_type = 'Final'"""

new_target = """                        if has_div or has_rd or is_agm:
                            found_amount = None
                            found_record_date = None
                            found_type = 'Final'
                            agm_date = None"""

if target in content:
    content = content.replace(target, new_target)
    print("Replaced target")
else:
    print("target not found")

with open('backend/ingest/nse_lib.py', 'w') as f:
    f.write(content)
