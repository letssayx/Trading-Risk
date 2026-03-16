import re
with open('backend/ui/templates/workbench.html', 'r') as f:
    content = f.read()

# Fix FII/DII Cash error
with open('backend/web/api/data/view_routes.py', 'r') as f:
    routes = f.read()
    if "'fii_dii_cash': models.FIIDIICash" in routes:
        print("fii_dii_cash is in view_routes.py")
    if "from backend.ingest import nse_models as models" in routes:
        print("models are correctly imported")
