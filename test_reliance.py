import sys
from backend.ingest.field_mapper import FieldMapper

mapper = FieldMapper()

texts = [
    "Dividend - Rs 10 Per Share (Face Value Rs 10)",
    "Dividend - Rs 6 Per share",
    "Dividend Rs 3 & Special Rs 3",
    "Dividend - Rs 6 Per Share and Special Dividend - Rs 10 Per Share",
    "Dividend - Re 0.40 Per Share"
]

for t in texts:
    amt, type_ = mapper._parse_dividend(t, 10.0)
    print(f"'{t}' -> {amt} ({type_})")
