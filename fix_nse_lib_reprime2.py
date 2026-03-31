# Wait, I didn't actually check if the regex match worked. Let's see if the file changed.
with open("backend/ingest/nse_lib.py", "r") as f:
    code = f.read()
if "temp_session" in code:
    print("Success, nse_lib.py was patched.")
else:
    print("Failed to patch. Let me write a python script to manually replace it without regex dotall.")
