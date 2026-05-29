import re

with open("backend/ui/static/js/rolloverTool.js", "r") as f:
    js = f.read()

# Let's just find the json.data block using a more robust search
match = re.search(r'if \(json\.data && Array\.isArray\(json\.data\)\) \{([\s\S]*?)\}', js)
if match:
    block = match.group(1)
    if "this.updateDynamicChart();" in block and "this.renderMatrix" not in block:
        new_block = block.replace("this.updateDynamicChart();", "this.updateDynamicChart();\n                this.renderMatrix(this.allData, isMoM);")
        js = js.replace(match.group(0), f"if (json.data && Array.isArray(json.data)) {{{new_block}}}")
        print("Updated json.data block")
else:
    print("Failed to find json.data block")


# Add BPS to the table inside analyzeSingle:
# In the original 61fb7b8 code, it looks like:
# const expiries = histData.map(d => d.date || d.expiry).reverse();
# const values = histData.map(d => d.rollover_pct).reverse();
# const spreads = histData.map(d => d.rollover_cost || 0).reverse();
bps_code = """
                        const expiries = histData.map(d => d.date || d.expiry).reverse();
                        const values = histData.map(d => d.rollover_pct).reverse();
                        const spreads = histData.map(d => d.rollover_cost || 0).reverse();
                        const bpsValues = histData.map(d => {
                            const fPrice = d.price !== undefined ? d.price : d.fut_price;
                            if (d.rollover_cost !== null && fPrice !== null && fPrice > 0) {
                                return ((d.rollover_cost / fPrice) * 10000).toFixed(1);
                            }
                            return "-";
                        }).reverse();
"""
js = re.sub(r'const expiries = histData\.map\([\s\S]*?0\)\.reverse\(\);', bps_code.strip(), js)

# Table replace
old_table_regex = r'let histTableHtml = `<table[\s\S]*?histTableHtml \+= `</tr></tbody></table>`;'
new_table_code = """
                        let histTableHtml = `<table style="width: 100%; margin-top: 10px; border-collapse: collapse; font-size: 0.85em; text-align: center;">
                            <thead style="background: #333;"><tr>`;
                        expiries.forEach(e => histTableHtml += `<th style="padding: 4px; color: #aaa;">${e}<br><span style="font-size:9px; color:#aaa;">Roll% | Spread | BPS</span></th>`);
                        histTableHtml += `</tr></thead><tbody><tr>`;
                        values.forEach(v => histTableHtml += `<td style="padding: 4px; border: 1px solid #444; color: #ff9800;">${v !== null && v !== undefined ? v + '%' : '-'}</td>`);
                        histTableHtml += `</tr><tr>`;
                        spreads.forEach(v => histTableHtml += `<td style="padding: 4px; border: 1px solid #444; color: ${v >= 0 ? '#60a5fa' : '#ff4d4d'};">${v}</td>`);
                        histTableHtml += `</tr><tr>`;
                        bpsValues.forEach(v => histTableHtml += `<td style="padding: 4px; border: 1px solid #444; color: #ffb74d;">${v}</td>`);
                        histTableHtml += `</tr></tbody></table>`;
"""
if re.search(old_table_regex, js):
    js = re.sub(old_table_regex, new_table_code.strip(), js)
    print("Replaced hist table")

with open("backend/ui/static/js/rolloverTool.js", "w") as f:
    f.write(js)
