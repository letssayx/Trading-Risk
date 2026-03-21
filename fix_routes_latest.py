with open("backend/web/api/data/view_routes.py", "r") as f:
    content = f.read()

import re

# Insert 'latest: Optional[bool] = False,' into list_data signature
content = re.sub(
    r"(sort_order: Optional\[str\] = Query\('asc', pattern='\^\(asc\|desc\)\$'\),)",
    r"\1\n    latest: Optional[bool] = False,",
    content
)

# Insert logic to handle latest
# Let's find: if symbol:
# Replace it with latest handling
latest_logic = """
    # Handle Latest Data flag
    if latest:
        # Find the max date for this model
        if hasattr(model, 'date'):
            date_col = model.date
        elif hasattr(model, 'trade_date'):
            date_col = model.trade_date
        elif hasattr(model, 'board_meeting_date'):
             date_col = model.board_meeting_date
        elif hasattr(model, 'meeting_date'):
             date_col = model.meeting_date
        elif hasattr(model, 'ex_date'):
             date_col = model.ex_date
        else:
            date_col = None

        if date_col:
            max_date = db.query(func.max(date_col)).scalar()
            if max_date:
                # Override start and end dates
                start_date = max_date.strftime('%Y-%m-%d')
                end_date = max_date.strftime('%Y-%m-%d')

    # Apply Symbol/Search Filter (if applicable)
    filters = []
"""
content = re.sub(
    r"(# Apply Symbol/Search Filter \(if applicable\)\n\s+filters = \[\])",
    latest_logic,
    content
)

with open("backend/web/api/data/view_routes.py", "w") as f:
    f.write(content)
