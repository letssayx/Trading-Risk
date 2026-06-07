import re
import os

filepath = 'backend/web/api/data/special_sit_routes.py'
with open(filepath, 'r') as f:
    content = f.read()

search = """                    if upcoming_cycles:
                        # Try to find a matching cycle type to use its date
                        matching_cycle = next((c for c in upcoming_cycles if c['type'] == expected_type), upcoming_cycles[0])
                        expected_highly_likely = matching_cycle['highly_likely_months'][0] if matching_cycle['highly_likely_months'] else "-"
                        if isinstance(expected_highly_likely, int):
                            expected_highly_likely = datetime.date(2000, expected_highly_likely, 1).strftime('%b')

                        m_names = [datetime.date(2000, m, 1).strftime('%b') for m in matching_cycle['less_likely_months']]
                        expected_less_likely = ", ".join(m_names) if m_names else "-"
                    else:
                        expected_highly_likely = "-"
                        expected_less_likely = "-" """

replace = """                    if upcoming_cycles:
                        # Try to find a matching cycle type to use its date
                        matching_cycle = next((c for c in upcoming_cycles if c['type'] == expected_type), upcoming_cycles[0])
                        expected_highly_likely = matching_cycle['highly_likely_months'][0] if matching_cycle['highly_likely_months'] else "-"
                        if isinstance(expected_highly_likely, int):
                            expected_highly_likely = datetime.date(2000, expected_highly_likely, 1).strftime('%b')

                        m_names = [datetime.date(2000, m, 1).strftime('%b') for m in matching_cycle['less_likely_months']]
                        expected_less_likely = "Amount declared, date not yet announced" # Overriding for ex-awaited
                    else:
                        expected_highly_likely = "-"
                        expected_less_likely = "Amount declared, date not yet announced" """

if search in content:
    content = content.replace(search, replace)
    with open(filepath, 'w') as f:
        f.write(content)
    print("special_sit_routes.py display patched")
else:
    print("Could not find the display block")
