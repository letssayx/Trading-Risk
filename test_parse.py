from backend.ingest.field_mapper import FieldMapper

texts = [
    ("Dividend - Re 0.50 Per Share", 2),
    ("Dividend - Re 0.40 Per Share", 2),
    ("Dividend - Rs 9 Per Share", 10),
]

for t, fv in texts:
    amt, type_ = FieldMapper._parse_dividend(t, fv)
    print(f"'{t}' -> {amt} ({type_})")
