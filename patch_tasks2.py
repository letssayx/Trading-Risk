import re

with open('backend/ingest/tasks.py', 'r') as f:
    content = f.read()

# First let's remove the T+1 block inside the first loop (`dedup_syns` loop)
block_to_remove1 = r"""                            # In India, T+1 settlement means Ex-Date is the same as Record Date
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

content = content.replace(block_to_remove1, "")

# Second let's remove the T+1 block inside the second loop (`group_officials` matching loop)
block_to_remove2 = r"""                                if syn.get('ex_date_obj') is None:
                                    syn_rd = off.get('record_date')
                                    if isinstance(syn_rd, str):
                                        import datetime
                                        try:
                                            syn['ex_date_obj'] = datetime.datetime.strptime(syn_rd, "%d-%b-%Y").date()
                                        except ValueError:
                                            syn['ex_date_obj'] = syn_rd
                                    else:
                                        syn['ex_date_obj'] = syn_rd
                                    syn['ex_date'] = syn_rd"""

content = content.replace(block_to_remove2, "")

# Now let's inject the universal T+1 logic right before final_actions.sort()
t1_logic = """
            # Universal T+1 Ex-Date Logic (India Market)
            for action in final_actions:
                if action.get('ex_date_obj') is None and action.get('record_date') is not None:
                    rec_date = action.get('record_date')
                    if isinstance(rec_date, str):
                        import datetime
                        try:
                            action['ex_date_obj'] = datetime.datetime.strptime(rec_date, "%d-%b-%Y").date()
                        except ValueError:
                            action['ex_date_obj'] = rec_date
                    else:
                        action['ex_date_obj'] = rec_date
                    action['ex_date'] = rec_date

            final_actions.sort(key=final_sort_key, reverse=True)"""

content = content.replace("            final_actions.sort(key=final_sort_key, reverse=True)", t1_logic)

with open('backend/ingest/tasks.py', 'w') as f:
    f.write(content)
