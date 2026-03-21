import sys
from backend.web.api.data.view_routes import process_results
from backend.ingest.nse_models import CorporateAction
import math

class DummyRow:
    def __init__(self, **kwargs):
        self.__table__ = type('Table', (), {'columns': [type('Col', (), {'name': k})() for k in kwargs.keys()]})()
        for k, v in kwargs.items():
            setattr(self, k, v)

rows = [DummyRow(id=1, parsed_dividend_amount=math.nan, symbol="TEST")]

res = process_results(rows, CorporateAction)
import json
print(json.dumps(res))
