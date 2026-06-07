import re

with open('./backend/web/api/data/special_sit_routes.py', 'r') as f:
    content = f.read()

search_pattern = r"""            # If the last event is Ex-Awaited \(amount declared, but no ex-date yet\)
            if history:
                latest = history\[0\]
                if latest\.get\('amount'\) and \(not latest\.get\('ex_date'\) or latest\.get\('ex_date'\) == 'Record date not yet declared'\):
                    expected_amount = latest\['amount'\]
                    expected_amount_compare = latest\['amount'\]
                    expected_type = latest\.get\('dividend_type', 'Interim'\)

                    # Sync the >2% flag for Ex-Awaited
                    is_above_2_percent = latest\.get\('is_above_2_percent', False\)

                    if upcoming_cycles:
                        # Try to find a matching cycle type to use its date
                        matching_cycle = next\(\(c for c in upcoming_cycles if c\['type'\] == expected_type\), upcoming_cycles\[0\]\)
                        expected_highly_likely = f"Forecasted: \{matching_cycle\['next_date'\]\.strftime\('%d-%m-%Y'\)\}"
                    else:
                        expected_highly_likely = "-"
                    expected_less_likely = "Amount declared, date not yet announced\""""

replace_block = """            # If the last event is Ex-Awaited (amount declared, but no ex-date yet)
            if history:
                latest = history[0]
                is_ex_awaited = False
                if latest.get('amount'):
                    ex_d = latest.get('ex_date')
                    if not ex_d or ex_d == 'Record date not yet declared':
                        is_ex_awaited = True
                    else:
                        try:
                            # If there is a date, check if it is active/upcoming. If it's already past, we shouldn't trigger Ex-Awaited warning.
                            import datetime as dt_lib
                            ex_dt = dt_lib.datetime.strptime(ex_d, "%d %b %Y").date()
                            if ex_dt >= dt_lib.date.today():
                                # It's announced, handled above
                                pass
                        except Exception:
                            is_ex_awaited = True

                if is_ex_awaited and expected_less_likely != 'Confirmed' and (not expected_highly_likely or not expected_highly_likely.startswith('Announced')):
                    expected_amount = latest['amount']
                    expected_amount_compare = latest['amount']
                    expected_type = latest.get('dividend_type', 'Interim')

                    # Sync the >2% flag for Ex-Awaited
                    is_above_2_percent = latest.get('is_above_2_percent', False)

                    if upcoming_cycles:
                        # Try to find a matching cycle type to use its date
                        matching_cycle = next((c for c in upcoming_cycles if c['type'] == expected_type), upcoming_cycles[0])
                        expected_highly_likely = f"Forecasted: {matching_cycle['next_date'].strftime('%d-%m-%Y')}"
                    else:
                        expected_highly_likely = "-"
                    expected_less_likely = "Amount declared, date not yet announced\""""

content = re.sub(search_pattern, replace_block, content)

with open('./backend/web/api/data/special_sit_routes.py', 'w') as f:
    f.write(content)
