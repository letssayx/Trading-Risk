import re
with open('backend/ingest/tasks.py', 'r') as f:
    content = f.read()

# Let's fix the is_ann_date_match issue which might overwrite consecutive dividends if they share the exact same announcement date (like both declared on same board meeting).
# Oh, if Q1 and Q2 are announced on the SAME day, and have the SAME amount? Is that possible? No.
# If they are announced on the SAME day, but different amounts, amount_conflict = True handles it.
# If they are announced on DIFFERENT days, but same amount... ad1 != ad2, so is_ann_date_match is False.

old_logic = """                    is_ex_date_match = (r_ex == r_ex_val) or (row.is_awaited and r_ex == datetime.date(1900, 1, 1) and r_ex_val != datetime.date(1900, 1, 1))
                    is_ann_date_match = (ad1 == ad2 and ad1 is not None)

                    if (is_ex_date_match or is_ann_date_match) and r_type == dividend_type_val:
                        matched_row = row
                        break"""

new_logic = """                    # EXPLICIT DATE MATCHING:
                    # We ONLY match if they share the exact same Ex-Date.
                    # Or, if the DB row is missing an ex-date (awaited), we can link it if it shares the exact same Announcement Date.
                    is_ex_date_match = (r_ex == r_ex_val and r_ex != datetime.date(1900, 1, 1))
                    is_awaited_match = (row.is_awaited and r_ex == datetime.date(1900, 1, 1) and r_ex_val != datetime.date(1900, 1, 1) and ad1 == ad2)

                    # If BOTH are missing an ex-date (1900-01-01), they are both awaited. Match by announcement date.
                    is_both_awaited_match = (r_ex == datetime.date(1900, 1, 1) and r_ex_val == datetime.date(1900, 1, 1) and ad1 == ad2)

                    if (is_ex_date_match or is_awaited_match or is_both_awaited_match) and r_type == dividend_type_val:
                        matched_row = row
                        break"""

if old_logic in content:
    content = content.replace(old_logic, new_logic)
    with open('backend/ingest/tasks.py', 'w') as f:
        f.write(content)
    print("Patched DB deduplication logic.")
else:
    print("Could not find DB dedup logic")
