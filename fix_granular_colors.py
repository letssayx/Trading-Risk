import re

file_path = "backend/ui/static/js/script_workbench2.js"
with open(file_path, "r") as f:
    content = f.read()

# renderParticipantGranular doesn't seem to define colors inline, or maybe it does? Let's check:
