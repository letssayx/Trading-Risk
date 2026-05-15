with open('backend/ingest/nse_lib.py', 'r') as f:
    content = f.read()

# Increase windows from 180 to 730 to ensure we catch very long-dated announcements (like BHEL in 2025/2026)
content = content.replace(
    'to_date_str = (trade_date + timedelta(days=180)).strftime("%d-%m-%Y")',
    'to_date_str = (trade_date + timedelta(days=730)).strftime("%d-%m-%Y")'
)

with open('backend/ingest/nse_lib.py', 'w') as f:
    f.write(content)
