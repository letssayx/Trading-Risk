import re

with open("backend/web/api/data/view_routes.py", "r") as f:
    content = f.read()

# I will replace the messy pivot logic block with a cleanly indented one
old_block = """            if type == 'mwpl':
            from collections import defaultdict
            grouped = defaultdict(dict)
            max_clients = 0

            for row in results:
                # Row is a SQLAlchemy model instance here, process_results will access its dict
                date_val = row.date.isoformat() if hasattr(row.date, 'isoformat') else str(row.date)
                key = (date_val, row.underlying_stock)
                client_num = row.client_position_num

                # Make sure we don't index error. The data has position_pct.
                grouped[key][f"Client {client_num}"] = row.position_pct
                max_clients = max(max_clients, client_num)

            pivoted = []
            for (date, stock), positions in grouped.items():
                row_dict = {
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

            # Sort by Date descending, then Total descending
            pivoted.sort(key=lambda x: (x["Date"], x["Total"]), reverse=True)

            # Add Sr No. after sort
            for idx, r in enumerate(pivoted, start=1):
                r["Sr No."] = idx

            return pivoted

        return process_results(results, model)"""

new_block = """            if type == 'mwpl':
                from collections import defaultdict
                grouped = defaultdict(dict)
                max_clients = 0

                for row in results:
                    # Row is a SQLAlchemy model instance here
                    date_val = row.date.isoformat() if hasattr(row.date, 'isoformat') else str(row.date)
                    key = (date_val, row.underlying_stock)
                    client_num = row.client_position_num

                    grouped[key][f"Client {client_num}"] = row.position_pct
                    max_clients = max(max_clients, client_num)

                pivoted = []
                for (date, stock), positions in grouped.items():
                    row_dict = {
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

                # Sort by Date descending, then Total descending
                pivoted.sort(key=lambda x: (x["Date"], x["Total"]), reverse=True)

                # Add Sr No. after sort
                for idx, r in enumerate(pivoted, start=1):
                    r["Sr No."] = idx

                return pivoted

            return process_results(results, model)"""

content = content.replace(old_block, new_block)

with open("backend/web/api/data/view_routes.py", "w") as f:
    f.write(content)
