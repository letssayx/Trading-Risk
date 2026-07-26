import re

with open('backend/ingest/tasks.py', 'r') as f:
    content = f.read()

# Remove the T+1 logic from inside the deduplication block:
block_to_remove = r"""                            # In India, T+1 settlement means Ex-Date is the same as Record Date
                            # Check ex-date explicitly outside the record_date condition
                            if ex.get('ex_date_obj') is None and ex.get('record_date') is not None:
                                syn_rd = ex.get('record_date')
                                if isinstance(syn_rd, str):
                                    import datetime
                                    try:
                                        ex['ex_date_obj'] = datetime.datetime.strptime(syn_rd, "%d-%b-%Y").date()
                                    except ValueError:
                                        ex['ex_date_obj'] = syn_rd
                                else:
                                    ex['ex_date_obj'] = syn_rd
                                ex['ex_date'] = syn_rd"""

# Find where chained_history is used at the end of the deduplication, and add T+1 logic there globally
replacement_at_end = """        for item in chained_history:
            # Universal T+1 Ex-Date Logic
            if item.get('ex_date_obj') is None and item.get('record_date') is not None:
                rec_date = item.get('record_date')
                if isinstance(rec_date, str):
                    try:
                        item['ex_date_obj'] = datetime.datetime.strptime(rec_date, "%d-%b-%Y").date()
                    except ValueError:
                        item['ex_date_obj'] = rec_date
                else:
                    item['ex_date_obj'] = rec_date
                item['ex_date'] = rec_date

        for entry in chained_history:"""

new_content = content.replace(block_to_remove, "")
new_content = new_content.replace("        for entry in chained_history:", replacement_at_end)

with open('backend/ingest/tasks.py', 'w') as f:
    f.write(new_content)
