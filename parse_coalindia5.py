from backend.ingest.field_mapper import FieldMapper

amount, type_ = FieldMapper._parse_dividend("To consider and approve the financial results for the period ended Jun 30, 2026 and dividend", 10.0)
print(f"Amount: {amount}, Type: {type_}")

amount, type_ = FieldMapper._parse_dividend("COAL INDIA LIMITED has informed the Exchange about Board Meeting to be held on 27-Apr-2026 to consider and approve the Yearly Audited Financial results of the Company for the period ended March 2026 and Dividend.", 10.0)
print(f"Amount: {amount}, Type: {type_}")
