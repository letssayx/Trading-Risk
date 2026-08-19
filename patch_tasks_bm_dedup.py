import re
with open('backend/ingest/tasks.py', 'r') as f:
    content = f.read()

# We also need to dedup BM intimations exactly the same way when appending them in Phase 2
old_bm_append = """                    final_actions.append({
                        "dividend_type": m.extracted_dividend_type,
                        "purpose": m.purpose,
                        "ex_date": ex_date_val.strftime("%Y-%m-%d") if ex_date_val else None,
                        "ex_date_obj": ex_date_val,
                        "broadcast_date": m.broadcast_date or m.date,
                        "announcement_date_obj": m.date,
                        "amount": m.extracted_dividend_amount,
                        "raw_amount": m.extracted_dividend_amount,
                        "face_value": None,
                        "agm_date": agm_date,
                        "record_date": bm_record_date,
                        "is_ca": False
                    })"""

new_bm_append = """                    new_bm_action = {
                        "dividend_type": m.extracted_dividend_type,
                        "purpose": m.purpose,
                        "ex_date": ex_date_val.strftime("%Y-%m-%d") if ex_date_val else None,
                        "ex_date_obj": ex_date_val,
                        "broadcast_date": m.broadcast_date or m.date,
                        "announcement_date_obj": m.date,
                        "amount": m.extracted_dividend_amount,
                        "raw_amount": m.extracted_dividend_amount,
                        "face_value": None,
                        "agm_date": agm_date,
                        "record_date": bm_record_date,
                        "is_ca": False
                    }

                    # STRICT DEDUPLICATION for awaited BMs:
                    is_bm_duplicate = False
                    for existing_act in final_actions:
                        if existing_act.get('amount') == new_bm_action.get('amount') and \\
                           existing_act.get('announcement_date_obj') == new_bm_action.get('announcement_date_obj') and \\
                           existing_act.get('dividend_type') == new_bm_action.get('dividend_type'):
                               is_bm_duplicate = True
                               break
                    if not is_bm_duplicate:
                        final_actions.append(new_bm_action)"""

if old_bm_append in content:
    content = content.replace(old_bm_append, new_bm_append)
    with open('backend/ingest/tasks.py', 'w') as f:
        f.write(content)
    print("Patched BM appending deduplication")
else:
    print("Could not find old BM append")
