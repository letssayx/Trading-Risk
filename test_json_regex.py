import re

text = """<reasoning>
The user's query specifies analyzing "Reliance's historical dividend payments," so the first step is to map "Reliance" to its official NSE symbol. The tool response confirms "RELIANCE" as the correct ticker for "RELIANCE INDUSTRIES." Other symbols like LTF or BAJFINANCE are irrelevant here. No months are specified in the query, and the focus is on historical data (not upcoming events). The summary clarifies the analysis scope: dividend sustainability assessment for RELIANCE using historical metrics.
</reasoning>
```json
{
  "widget": "dividend_table",
  "symbols": [
    "RELIANCE"
  ],
  "months": [],
  "upcoming": false,
  "summary": "Extracted RELIANCE as the target symbol for historical dividend sustainability analysis. No timeframe specified."
}
```
"""

# Current approach
raw_text = text
json_match = re.search(r'(\{.*\})', raw_text.replace('\n', ''), re.DOTALL)
print("Current Approach:", json_match.group(1) if json_match else 'None')

# Better approach
json_match2 = re.search(r'(\{[\s\S]*\})', raw_text)
print("\nBetter Approach:", json_match2.group(1) if json_match2 else 'None')
