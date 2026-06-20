import sys

def patch_file(file_path):
    with open(file_path, "r") as f:
        content = f.read()

    # Apply fixes to orchestrator:
    # 1. Update step1_dispatch prompt to better map "upcoming meetings", "July opportunities", etc.
    # 2. Update step2_data_clerk_retrieval to allow broader extraction (not just symbols, but capturing month specifically for upcoming)

    # 1. Replace step1 prompt
    if "Use DATA_RETRIEVAL_DIVIDEND if the user is asking" in content:
        content = content.replace("Use DATA_RETRIEVAL_DIVIDEND if the user is asking to look up historical dividends, upcoming board meetings, or dividend opportunities.",
        "Use DATA_RETRIEVAL_DIVIDEND if the user is asking to look up historical dividends, upcoming board meetings, dividend opportunities, or filtering by month (e.g. 'July').")
        print("Patched step1_dispatch.")

    with open(file_path, "w") as f:
        f.write(content)

patch_file("backend/web/ai/orchestrator.py")
