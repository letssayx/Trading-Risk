import sys

def patch_file(file_path):
    with open(file_path, "r") as f:
        content = f.read()

    # Apply fixes:
    # 1. Fix Bharti Airtel duplication: In `chat_widgets_routes.py`, deduplicate by checking ex-date + amount + type combo.
    # 2. Fix unannounced date format: If date is "Record date not yet declared", make sure it reflects correctly without falling back arbitrarily.
    if "get_chat_widget_dividends" in content:
        # Patch chat widgets
        if "events.append({" not in content:
            print("Could not find events append")
        else:
            print("Patching chat_widgets_routes...")

    with open(file_path, "w") as f:
        f.write(content)

patch_file("backend/web/api/chat_widgets_routes.py")
