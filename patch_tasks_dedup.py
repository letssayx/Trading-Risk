import re
with open('backend/ingest/tasks.py', 'r') as f:
    content = f.read()

# Instead of blindly appending CA records to ca_by_symbol, let's dedup them on exactly what the user said:
# "same amount and same date and same dividend type"

old_ca_append = """            ca_by_symbol[sym].append({
                "ex_date": ex_date_val.strftime("%Y-%m-%d") if ex_date_val else None,
                "ex_date_obj": ex_date_val,
                "announcement_date_obj": final_ann_date,
                "broadcast_date": final_broadcast,
                "dividend_type": r.dividend_type,
                "purpose": r.purpose,
                "amount": parsed_amount,
                "raw_amount": parsed_amount,
                "face_value": r.face_value if hasattr(r, 'face_value') else None,
                "record_date": r.record_date if hasattr(r, 'record_date') else None,
                "is_ca": True
            })"""

new_ca_append = """            new_ca = {
                "ex_date": ex_date_val.strftime("%Y-%m-%d") if ex_date_val else None,
                "ex_date_obj": ex_date_val,
                "announcement_date_obj": final_ann_date,
                "broadcast_date": final_broadcast,
                "dividend_type": r.dividend_type,
                "purpose": r.purpose,
                "amount": parsed_amount,
                "raw_amount": parsed_amount,
                "face_value": r.face_value if hasattr(r, 'face_value') else None,
                "record_date": r.record_date if hasattr(r, 'record_date') else None,
                "is_ca": True
            }

            # STRICT DEDUPLICATION: If we already have a CA with the EXACT same amount, ex-date, and dividend type, do not append it.
            is_duplicate = False
            for existing_ca in ca_by_symbol[sym]:
                if existing_ca.get('amount') == new_ca.get('amount') and \\
                   existing_ca.get('ex_date') == new_ca.get('ex_date') and \\
                   existing_ca.get('dividend_type') == new_ca.get('dividend_type'):
                       is_duplicate = True
                       break
            if not is_duplicate:
                ca_by_symbol[sym].append(new_ca)"""

if old_ca_append in content:
    content = content.replace(old_ca_append, new_ca_append)
    with open('backend/ingest/tasks.py', 'w') as f:
        f.write(content)
    print("Patched CA appending deduplication")
else:
    print("Could not find old CA append")
