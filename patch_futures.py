import sys

filepath = 'backend/web/api/data/view_routes.py'
with open(filepath, 'r') as f:
    content = f.read()

import re

# We want to change instrument_type.like('FUT%') to instrument_type.in_(['FUTSTK', 'FUTIDX'])
# Wait, actually let's use replace_with_git_merge_diff
