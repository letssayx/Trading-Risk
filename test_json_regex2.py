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

raw_text = text
# Extract JSON block
json_match = re.search(r'(\{[\s\S]*\})', raw_text)
if json_match:
    widget_json_str = json_match.group(1)
else:
    # Fallback cleanup
    clean_text = re.sub(r'<reasoning>[\s\S]*?</reasoning>', '', raw_text, flags=re.IGNORECASE).strip()
    # Strip out any markdown formatting
    clean_text = re.sub(r'```json\s*', '', clean_text)
    clean_text = re.sub(r'```\s*', '', clean_text)
    if clean_text.startswith('{'):
        widget_json_str = clean_text

print(widget_json_str)
