import re

file_path = "backend/ui/templates/workbench.html"
with open(file_path, "r") as f:
    content = f.read()

# Let's fix the pct_away names and other stuff if they are mismatched.
# We will use exactly what's expected by the frontend table.
# generateTableHTML expects:
# pct_away_highest_pe, pct_away_highest_ce, highest_oi_pe_premium, highest_oi_ce_premium
# highest_oi_pe_oi, highest_oi_ce_oi
