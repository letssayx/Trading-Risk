import sys
import os

# Add repo root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.infrastructure.registry import ToolboxRegistry

def run_debug():
    print("--- Debugging Registry Discovery ---")
    ToolboxRegistry.auto_discover()

    widgets = ToolboxRegistry.get_widgets()
    print(f"\n[RESULT] Registered {len(widgets)} widgets.")

    names = [w['title'] for w in widgets]
    print(f"Widget Names: {names}")

    required = ["Spread Synthesizer", "FICO Tool", "Z-Score Filter", "Turtle N-Calc"]
    missing = [r for r in required if r not in names]

    if missing:
        print(f"[ERROR] Missing required widgets: {missing}")
        sys.exit(1)
    else:
        print("[SUCCESS] All required widgets found.")

if __name__ == "__main__":
    run_debug()
