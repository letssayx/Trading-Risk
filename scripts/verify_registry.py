import sys
import os
sys.path.append(os.getcwd())

from backend.infrastructure.registry import ToolboxRegistry

print("Starting verification...")
try:
    ToolboxRegistry.auto_discover()
    tools = ToolboxRegistry.get_all_tools()
    print(f"Found {len(tools)} tools.")
    for t in tools:
        print(f" - {t['name']} ({t['category']}): {t['description']}")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
