from datetime import datetime, date
import pandas as pd

class DummyCol:
    def __init__(self, name):
        self.name = name

class DummyRow:
    def __init__(self, **kwargs):
        self.__table__ = type('obj', (object,), {'columns': [DummyCol(k) for k in kwargs.keys()]})()
        for k, v in kwargs.items():
            setattr(self, k, v)

def process_results(results, model=None, skip_instrument_type=False):
    import math
    data = []
    for row in results:
        row_dict = {}
        for col in row.__table__.columns:
            val = getattr(row, col.name)
            if isinstance(val, pd.Timestamp):
                val = val.to_pydatetime().isoformat()
            elif isinstance(val, datetime):
                val = val.isoformat()
            elif hasattr(val, 'isoformat'): # date
                val = val.isoformat()
            elif isinstance(val, float):
                if math.isnan(val) or math.isinf(val):
                    val = None
            row_dict[col.name] = val
        data.append(row_dict)
    return data

r1 = DummyRow(dt=datetime(2023, 1, 1, 12, 34, 56), dt2=date(2023,1,1), ts=pd.Timestamp('2023-01-01 12:34:56'))
print(process_results([r1]))
