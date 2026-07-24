with open('backend/ingest/tasks.py', 'r') as f:
    content = f.read()

search_block = """
            logs = db.query(ImportLog).filter(
                and_(
                    ImportLog.date >= start_date,
                    ImportLog.date <= end_date,
                    ImportLog.status == 'SUCCESS'
                )
            ).all()

            for log in logs:
                if log.date not in completed_map:
                    completed_map[log.date] = set()
                completed_map[log.date].add(log.pattern)
"""

replace_block = """
            logs = db.query(ImportLog).filter(
                and_(
                    ImportLog.import_date >= start_date,
                    ImportLog.import_date <= end_date,
                    ImportLog.status == 'SUCCESS'
                )
            ).all()

            for log in logs:
                # the column in DB is table_name, but previously someone used log.pattern? Let's check nse_models.py
                # Yes, table_name
                d = log.import_date
                if d not in completed_map:
                    completed_map[d] = set()
                completed_map[d].add(log.table_name)
"""

if search_block in content:
    content = content.replace(search_block, replace_block)
else:
    print("Block not found!")

with open('backend/ingest/tasks.py', 'w') as f:
    f.write(content)
