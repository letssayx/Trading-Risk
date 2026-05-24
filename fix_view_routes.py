import re

with open('backend/web/api/data/view_routes.py', 'r') as f:
    content = f.read()

# Replace the serialization block in process_results
old_block = """            val = getattr(row, col.name)
            if isinstance(val, pd.Timestamp):
                val = val.to_pydatetime().isoformat()
            elif isinstance(val, datetime):
                val = val.isoformat()
            elif hasattr(val, 'isoformat'): # date
                val = val.isoformat()
            elif isinstance(val, float):"""

new_block = """            val = getattr(row, col.name)
            if hasattr(val, 'strftime'):
                if hasattr(val, 'hour'):
                    val = val.strftime('%Y-%m-%dT%H:%M:%S')
                else:
                    val = val.strftime('%Y-%m-%d')
            elif isinstance(val, float):"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open('backend/web/api/data/view_routes.py', 'w') as f:
        f.write(content)
    print("Replaced successfully!")
else:
    print("Block not found!")
