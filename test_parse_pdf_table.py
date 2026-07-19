def process_table_for_record_date(table):
    if not table: return None
    # table is a list of lists (rows of columns)

    # 1. find index of 'Record Date' column
    record_date_col_idx = -1
    for i, row in enumerate(table):
        for j, cell in enumerate(row):
            if cell and 'record date' in str(cell).lower():
                record_date_col_idx = j
                break
        if record_date_col_idx != -1:
            # check rows below this header
            for k in range(i + 1, len(table)):
                val = table[k][record_date_col_idx]
                if val:
                    val = str(val).strip().replace('\n', ' ')
                    # Look for date pattern like 'Friday, July 24, 2026' or '24-Jul-2026'
                    import re
                    m = re.search(r'([a-zA-Z]+\s+\d{1,2}(?:st|nd|rd|th)?,\s*\d{4}|\d{1,2}(?:st|nd|rd|th)?[- \.][a-zA-Z]+[- \.]\d{4})', val)
                    if m:
                        return m.group(1).strip()
            break

    return None

mock_table = [
    ["Symbol", "Type", "Record Date", "Purpose"],
    ["BHARTIARTL", "Equity", "Friday, July 24, 2026\n", "Dividend"]
]

print(process_table_for_record_date(mock_table))
