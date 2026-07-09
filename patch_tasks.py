import re

with open("backend/ingest/tasks.py", "r") as f:
    content = f.read()

# 1. Update ca_by_symbol append to include record_date
content = content.replace('''                    "face_value": r.face_value if hasattr(r, 'face_value') else None
                })''', '''                    "face_value": r.face_value if hasattr(r, 'face_value') else None,
                    "record_date": r.record_date if hasattr(r, 'record_date') else None
                })''')

# 2. Update the standalone BM append to include record_date
content = content.replace('''                            "amount": amt,
                            "raw_amount": amt,
                            "face_value": None
                        })''', '''                            "amount": amt,
                            "raw_amount": amt,
                            "face_value": None,
                            "record_date": None
                        })''')

# 3. Update the insert in DividendDatabank to include record_date
content = content.replace('''                    raw_amount=h.get('raw_amount'),
                    face_value=h.get('face_value'),
                    purpose=h.get('purpose'),
                    is_awaited=is_awaited
                ))''', '''                    raw_amount=h.get('raw_amount'),
                    face_value=h.get('face_value'),
                    purpose=h.get('purpose'),
                    is_awaited=is_awaited,
                    record_date=h.get('record_date')
                ))''')

with open("backend/ingest/tasks.py", "w") as f:
    f.write(content)
