from backend.ingest.field_mapper import FieldMapper
purpose = "CONTAINER CORPORATION OF INDIA LIMITED has informed the Exchange about Board Meeting to be held on 29-Oct-2024 to consider and approve the Half Yearly Unaudited Financial results of the Company for the period ended September 2024 and Dividend."
amount, type = FieldMapper._parse_dividend(purpose, 5)
print(f"Amount: {amount}, Type: {type}")

purpose2 = "Board of Directors at its meeting held on May 25, 2024, recommended Final Dividend of Re. 1 per equity share."
amount2, type2 = FieldMapper._parse_dividend(purpose2, 5)
print(f"Amount: {amount2}, Type: {type2}")
