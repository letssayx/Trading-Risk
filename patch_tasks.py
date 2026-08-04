import re

with open('backend/ingest/tasks.py', 'r') as f:
    content = f.read()

# Fix the AGM forced merge issue
old_logic = """                        # If diff is exactly 0 (same day) and it's a generic dividend vs a specific one, or amount is missing in one, forcefully merge
                        # EXCEPTION: Do NOT forcefully merge AGMs. Let them stand alone.
                        if diff == 0 and (syn_type in ['-', 'Dividend'] or ex_type in ['-', 'Dividend']):
                            if not amounts_conflict and not records_conflict:
                                is_potential_duplicate = True"""

new_logic = """                        # If diff is exactly 0 (same day) and it's a generic dividend vs a specific one, or amount is missing in one, forcefully merge
                        # EXCEPTION: Do NOT forcefully merge AGMs. Let them stand alone.
                        if diff == 0 and (syn_type in ['-', 'Dividend'] or ex_type in ['-', 'Dividend']):
                            if syn_type != 'AGM' and ex_type != 'AGM':
                                if not amounts_conflict and not records_conflict:
                                    is_potential_duplicate = True"""

if old_logic in content:
    content = content.replace(old_logic, new_logic)
    print("Patched AGM forced merge issue.")
else:
    print("Could not find old_logic for AGM forced merge.")

with open('backend/ingest/tasks.py', 'w') as f:
    f.write(content)
