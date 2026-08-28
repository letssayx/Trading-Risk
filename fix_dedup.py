import re

with open('backend/ingest/tasks.py', 'r') as f:
    content = f.read()

# Fix Deduplication Logic in tasks.py
# 1. Update the deduplication logic to ensure strict priority for specific types like 'Final' and 'Interim' over 'AGM', 'Dividend', or '-'.
# 2. Fix the Broadcast Date propagation when merging synthetics (Board Meetings) with officials (Corporate Actions)

def replace_block(content, start_str, end_str, new_block):
    start = content.find(start_str)
    if start == -1: return content
    end = content.find(end_str, start)
    if end == -1: return content
    end += len(end_str)
    return content[:start] + new_block + content[end:]

# Fix 1: Better Type Upgrades during Deduction of Synthetics
new_syn_dedup = """                        # Fix Deduplication: General Updates and Record Date announcements happen for the same event.
                        # Deduplicate them strictly if symbol + div_type matches within window.
                        # E.g. COALINDIA duplicates have exactly the same symbol and type (like Interim) within days of each other.
                        # Do NOT merge different dividend types (like Interim and Final) even if they happen on the same day.
                        is_duplicate_event = (syn_type == ex_type)

                        # Only allow fallback to general 'Dividend' / '-' if the other is a specific dividend type,
                        # but do not merge 'Interim' with 'Final'

                        is_potential_duplicate = is_duplicate_event
                        upgrade_syn_type = None
                        upgrade_ex_type = None

                        if not is_potential_duplicate:
                            generic_types = ['-', 'Dividend', 'AGM']
                            specific_types = ['Interim', 'Final', 'Special']

                            if syn_type in generic_types and ex_type in (specific_types + generic_types):
                                is_potential_duplicate = True
                                if ex_type in specific_types:
                                    upgrade_syn_type = ex_type
                            elif ex_type in generic_types and syn_type in (specific_types + generic_types):
                                is_potential_duplicate = True
                                if syn_type in specific_types:
                                    upgrade_ex_type = syn_type

                        # STRICT Deduplication Check:
                        # Do NOT merge if they both have explicit, differing record dates,
                        # OR if they both have explicit, differing amounts.
                        # This prevents squashing Interim and Final dividends announced on the same day into one row.

                        syn_amount = syn.get('amount')
                        ex_amount = ex.get('amount')
                        syn_rec = syn.get('record_date')
                        ex_rec = ex.get('record_date')

                        amounts_conflict = (syn_amount is not None and str(syn_amount) != '-' and
                                            ex_amount is not None and str(ex_amount) != '-' and
                                            syn_amount != ex_amount)

                        records_conflict = (syn_rec is not None and ex_rec is not None and syn_rec != ex_rec)

                        if amounts_conflict or records_conflict:
                            is_potential_duplicate = False

                        # If diff is exactly 0 (same day) and it's a generic dividend vs a specific one, or amount is missing in one, forcefully merge
                        if diff == 0 and (syn_type in generic_types or ex_type in generic_types):
                            if not amounts_conflict and not records_conflict:
                                is_potential_duplicate = True
                                # ensure we don't accidentally wipe out specific tags during exact matches later
                                if ex_type not in generic_types and syn_type in generic_types:
                                    syn['dividend_type'] = ex_type
                                elif syn_type not in generic_types and ex_type in generic_types:
                                    ex['dividend_type'] = syn_type"""

content = replace_block(content,
    "                        # Fix Deduplication: General Updates and Record Date announcements happen for the same event.",
    "                                    ex['dividend_type'] = syn_type",
    new_syn_dedup)

# Fix 2: Better Broadcast Date & Type Inheriting for Final Merge
new_final_merge = """                            if off.get('agm_date'):
                                syn['agm_date'] = off.get('agm_date')

                            if not off_m or (syn_m and safe_date(syn_m.meeting_date) > safe_date(off_m.meeting_date)):
                                off['_matchedMeeting'] = syn_m

                            # Ensure that generic 'AGM' or 'Dividend' updates do not wipe out specific 'Interim'/'Final' types
                            syn_type_val = syn.get('dividend_type')
                            off_type_val = off.get('dividend_type')
                            generic_types = ['-', 'Dividend', 'AGM']

                            if syn_type_val and syn_type_val not in generic_types:
                                if not off_type_val or off_type_val in generic_types:
                                    off['dividend_type'] = syn_type_val

                            if off_type_val and off_type_val not in generic_types:
                                if not syn_type_val or syn_type_val in generic_types:
                                    syn['dividend_type'] = off_type_val

                            if syn.get('record_date') is not None and off.get('record_date') is None:
                                off['record_date'] = syn.get('record_date')

                            if syn.get('agm_date') is not None and off.get('agm_date') is None:
                                off['agm_date'] = syn.get('agm_date')

                            # Inherit the original broadcast date of the Board Meeting so late AGM announcements
                            # don't falsely bump the declaration date.
                            # ALWAYS trust the synthetic (Board Meeting) broadcast date over the official (Corporate Action/Update)
                            # if the board meeting actually declared the dividend (has amount).
                            if syn.get('broadcast_date'):
                                if syn.get('amount') is not None or syn_type_val not in generic_types:
                                    off['broadcast_date'] = syn.get('broadcast_date')
                                    off['announcement_date_obj'] = syn.get('broadcast_date')"""

content = replace_block(content,
    "                            if off.get('agm_date'):",
    "                                        off['announcement_date_obj'] = syn.get('broadcast_date')",
    new_final_merge)

with open('backend/ingest/tasks.py', 'w') as f:
    f.write(content)
print("Updated tasks.py successfully.")
