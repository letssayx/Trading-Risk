with open("backend/analysis/toolbox/reports/morning_report.py", "r") as f:
    text = f.read()

text = text.replace(
    "record.near_expiry_date = near_fut.expiry_date if near_fut else None",
    "record.near_expiry_date = near_fut.expiry_date if near_fut else None"
)
text = text.replace(
    "record.next_expiry_date = next_fut.expiry_date if next_fut else None",
    "record.next_expiry_date = next_fut.expiry_date if next_fut else None"
)
text = text.replace(
    "record.far_expiry_date = far_fut.expiry_date if far_fut else None",
    "record.far_expiry_date = far_fut.expiry_date if far_fut else None"
)

# wait these are already set correctly! Let's verify why they were shown as empty in the screenshot.
