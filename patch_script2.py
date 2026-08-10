with open('backend/ingest/tasks.py', 'r') as f:
    content = f.read()

# Fix sorting fallback diff_days which allows linking future CAs to past broadcasts
search_5 = """                                if not a_date and (a_purpose.find('not yet declared') != -1 or a_purpose.find('dividend (') != -1 or a_purpose.find('dividend') != -1):
                                    is_time_match = True
                                    if a.get('broadcast_date') and m.meeting_date:
                                        b_date = a.get('broadcast_date')
                                        if hasattr(b_date, 'date'): b_date = b_date.date()
                                        meet_date = m.meeting_date
                                        if hasattr(meet_date, 'date'): meet_date = meet_date.date()
                                        diff_days = abs((b_date - meet_date).days)
                                        if diff_days > 30: is_time_match = False"""

replace_5 = """                                if not a_date and (a_purpose.find('not yet declared') != -1 or a_purpose.find('dividend (') != -1 or a_purpose.find('dividend') != -1):
                                    is_time_match = True
                                    if a.get('broadcast_date') and m.meeting_date:
                                        b_date = a.get('broadcast_date')
                                        if hasattr(b_date, 'date'): b_date = b_date.date()
                                        meet_date = m.meeting_date
                                        if hasattr(meet_date, 'date'): meet_date = meet_date.date()
                                        diff_days = (b_date - meet_date).days
                                        if not (0 <= diff_days <= 30): is_time_match = False"""

content = content.replace(search_5, replace_5)

with open('backend/ingest/tasks.py', 'w') as f:
    f.write(content)
