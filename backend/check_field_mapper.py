import sys
sys.path.insert(0, 'backend')
from ingest.field_mapper import FieldMapper

# Quick check if parse_nse_datetime exists
print(hasattr(FieldMapper, 'parse_nse_datetime'))
try:
    from ingest.field_mapper import parse_nse_datetime
    print("Yes")
except ImportError:
    print("No parse_nse_datetime found globally")
