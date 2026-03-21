from collections import defaultdict
import datetime

results = [
    {"date": "2023-01-01", "underlying_stock": "AAPL", "client_position_num": 1, "position_pct": 5.5},
    {"date": "2023-01-01", "underlying_stock": "AAPL", "client_position_num": 2, "position_pct": 4.2},
    {"date": "2023-01-01", "underlying_stock": "MSFT", "client_position_num": 1, "position_pct": 8.1},
    {"date": "2023-01-02", "underlying_stock": "AAPL", "client_position_num": 1, "position_pct": 6.0},
]

def pivot_mwpl(data):
    # Group by (date, underlying_stock)
    grouped = defaultdict(dict)
    max_clients = 0

    for row in data:
        key = (row['date'], row['underlying_stock'])
        client_num = row['client_position_num']
        grouped[key][f"Client {client_num}"] = row['position_pct']
        max_clients = max(max_clients, client_num)

    pivoted = []
    sr_no = 1
    for (date, stock), positions in grouped.items():
        row_dict = {
            "Sr No.": sr_no,
            "Date": date,
            "Underlying Stock": stock,
        }
        total = 0
        for i in range(1, max_clients + 1):
            client_key = f"Client {i}"
            val = positions.get(client_key, None)
            row_dict[client_key] = val
            if val is not None:
                total += val

        row_dict["Total"] = round(total, 2)
        pivoted.append(row_dict)
        sr_no += 1

    # Sort by Total descending by default, then date descending
    pivoted.sort(key=lambda x: (x["Date"], x["Total"]), reverse=True)
    return pivoted

print(pivot_mwpl(results))
