import re

with open("backend/web/api/data/special_sit_routes.py", "r") as f:
    content = f.read()

# We need to insert the deduplication logic for bms before they are appended
# Look for the section:
#         # Append remaining BMs that haven't dropped an official CA yet (Upcoming Dividends/Intimations)
#         for bm in bms:

search_str = """        # Append remaining BMs that haven't dropped an official CA yet (Upcoming Dividends/Intimations)
        for bm in bms:"""

replace_str = """        # Deduplicate synthetics (multiple board meetings for the same event) before appending
        # Sort newest first
        bms.sort(key=lambda x: x.meeting_date or x.broadcast_date or x.date or datetime.date.min, reverse=True)

        deduplicated_bms = []
        for bm in bms:
            is_duplicate = False
            bm_date = bm.meeting_date or bm.broadcast_date or bm.date
            if hasattr(bm_date, 'date'):
                bm_date = bm_date.date()

            for existing in deduplicated_bms:
                existing_date = existing.meeting_date or existing.broadcast_date or existing.date
                if hasattr(existing_date, 'date'):
                    existing_date = existing_date.date()

                if bm_date and existing_date:
                    diff_days = abs((bm_date - existing_date).days)
                    # Merge synthetics if they are within 60 days of each other and have the same dividend type
                    if diff_days <= 60 and bm.extracted_dividend_type == existing.extracted_dividend_type:
                        is_duplicate = True
                        # Update amount if the newer duplicate has it
                        if not existing.extracted_dividend_amount and bm.extracted_dividend_amount:
                            existing.extracted_dividend_amount = bm.extracted_dividend_amount
                        break

            if not is_duplicate:
                deduplicated_bms.append(bm)

        # Append remaining deduplicated BMs that haven't dropped an official CA yet (Upcoming Dividends/Intimations)
        for bm in deduplicated_bms:"""

if search_str in content:
    content = content.replace(search_str, replace_str)
    with open("backend/web/api/data/special_sit_routes.py", "w") as f:
        f.write(content)
    print("Patched successfully")
else:
    print("Could not find target string to patch.")
