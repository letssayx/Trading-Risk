with open('backend/ingest/tasks.py', 'r') as f:
    content = f.read()

# 1. Filter out Intimation board meetings
search_1 = """            # 1. Synthesize Board Meetings into Actions if they don't have one
            for m in bms:
                purpose_lower = (m.purpose or '').lower()
                has_amount = m.extracted_dividend_amount is not None"""
replace_1 = """            # 1. Synthesize Board Meetings into Actions if they don't have one
            for m in bms:
                purpose_lower = (m.purpose or '').lower()

                # Prevent Intimations from prematurely setting dividends
                if 'intimation' in purpose_lower and 'outcome' not in purpose_lower:
                    continue

                has_amount = m.extracted_dividend_amount is not None"""
content = content.replace(search_1, replace_1)

# 2. Fix abs() diff_days to forward window
search_2 = """                                if a_date and a_date >= m_date:
                                    diff_days = abs((a_date - m_date).days)
                                    if diff_days <= 180:"""
replace_2 = """                                if a_date and a_date >= m_date:
                                    diff_days = (a_date - m_date).days
                                    if 0 <= diff_days <= 180:"""
content = content.replace(search_2, replace_2)

# 3. Fix negative linkage window
search_3 = """                        diff_days = (off_date_val - syn_date_val).days
                        if -10 <= diff_days <= 180 and (syn.get('dividend_type') == off.get('dividend_type') or syn.get('dividend_type') == '-' or off.get('dividend_type') == '-'):"""
replace_3 = """                        diff_days = (off_date_val - syn_date_val).days
                        if 0 <= diff_days <= 180 and (syn.get('dividend_type') == off.get('dividend_type') or syn.get('dividend_type') == '-' or off.get('dividend_type') == '-'):"""
content = content.replace(search_3, replace_3)

# 4. Sort chronologically
search_4 = """            # Sort chronologically
            def final_sort_key(x):
                t = safe_date(x.get('ex_date_obj'))
                if t != datetime.date.min: return t
                t = safe_date(x.get('announcement_date_obj') or x.get('broadcast_date'))
                if t != datetime.date.min: return t
                m = x.get('_matchedMeeting')
                if m:
                    t = safe_date(m.meeting_date)
                    if t != datetime.date.min: return t
                t = safe_date(x.get('date'))
                return t"""
replace_4 = """            # Sort chronologically to preserve the event timeline
            def final_sort_key(x):
                ex_d = safe_date(x.get('ex_date_obj'))
                if ex_d != datetime.date.min:
                    return ex_d

                m = x.get('_matchedMeeting')
                if m:
                    bm_d = safe_date(m.meeting_date if hasattr(m, 'meeting_date') and m.meeting_date else m.date)
                    if bm_d != datetime.date.min:
                        return bm_d

                ann_d = safe_date(x.get('announcement_date_obj') or x.get('broadcast_date'))
                if ann_d != datetime.date.min:
                    return ann_d

                return safe_date(x.get('date'))"""
content = content.replace(search_4, replace_4)

with open('backend/ingest/tasks.py', 'w') as f:
    f.write(content)
