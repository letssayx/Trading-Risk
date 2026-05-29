import re

with open("backend/ui/static/js/rolloverTool.js", "r") as f:
    js = f.read()

# 1. Add this.renderMatrix(this.allData, isMoM) into loadAggregatedData
load_data_match = re.search(r'if \(json\.data && Array\.isArray\(json\.data\)\) \{[\s\S]*?this\.updateDynamicChart\(\);\s*\}', js)
if load_data_match:
    original = load_data_match.group(0)
    if "this.renderMatrix" not in original:
        new_str = original.replace("this.updateDynamicChart();", "this.updateDynamicChart();\n                this.renderMatrix(this.allData, isMoM);")
        js = js.replace(original, new_str)
else:
    print("Could not find json.data block in loadAggregatedData")


# 2. Re-add BPS to analyzeSingle (it looks like my previous replace failed because of exact string matching issues)
# We will find where `const expiries` is mapped and replace that whole block.
analyze_single_match = re.search(r'const expiries = histData\.map\(\(d\) => d\.date \|\| d\.expiry\)\.reverse\(\);\s*const values = histData\.map\(\(d\) => d\.rollover_pct\)\.reverse\(\);\s*const spreads = histData\.map\(\(d\) => d\.rollover_cost \|\| 0\)\.reverse\(\);', js)
if analyze_single_match:
    bps_js = """                        const expiries = histData.map(d => d.date || d.expiry).reverse();
                        const values = histData.map(d => d.rollover_pct).reverse();
                        const spreads = histData.map(d => d.rollover_cost || 0).reverse();
                        const bpsValues = histData.map(d => {
                            const fPrice = d.price !== undefined ? d.price : d.fut_price;
                            if (d.rollover_cost !== null && fPrice !== null && fPrice > 0) {
                                return ((d.rollover_cost / fPrice) * 10000).toFixed(1);
                            }
                            return "-";
                        }).reverse();"""
    js = js.replace(analyze_single_match.group(0), bps_js)
else:
    # Handle arrow functions without parens
    analyze_single_match = re.search(r'const expiries = histData\.map\(d => d\.date \|\| d\.expiry\)\.reverse\(\);\s*const values = histData\.map\(d => d\.rollover_pct\)\.reverse\(\);\s*const spreads = histData\.map\(d => d\.rollover_cost \|\| 0\)\.reverse\(\);', js)
    if analyze_single_match:
        bps_js = """                        const expiries = histData.map(d => d.date || d.expiry).reverse();
                        const values = histData.map(d => d.rollover_pct).reverse();
                        const spreads = histData.map(d => d.rollover_cost || 0).reverse();
                        const bpsValues = histData.map(d => {
                            const fPrice = d.price !== undefined ? d.price : d.fut_price;
                            if (d.rollover_cost !== null && fPrice !== null && fPrice > 0) {
                                return ((d.rollover_cost / fPrice) * 10000).toFixed(1);
                            }
                            return "-";
                        }).reverse();"""
        js = js.replace(analyze_single_match.group(0), bps_js)

# Replace table in analyzeSingle
old_table_match = re.search(r'let histTableHtml = `<table[\s\S]*?</thead><tbody><tr>`;\s*values\.forEach\([^;]+;\s*histTableHtml \+= `</tr><tr>`;\s*spreads\.forEach\([^;]+;\s*histTableHtml \+= `</tr></tbody></table>`;', js)
if old_table_match:
    new_table = """                        let histTableHtml = `<table style="width: 100%; margin-top: 10px; border-collapse: collapse; font-size: 0.85em; text-align: center;">
                            <thead style="background: #333;"><tr>`;
                        expiries.forEach(e => histTableHtml += `<th style="padding: 4px; color: #aaa;">${e}<br><span style="font-size:9px; color:#aaa;">Roll% | Spread | BPS</span></th>`);
                        histTableHtml += `</tr></thead><tbody><tr>`;
                        values.forEach(v => histTableHtml += `<td style="padding: 4px; border: 1px solid #444; color: #ff9800;">${v !== null && v !== undefined ? v + '%' : '-'}</td>`);
                        histTableHtml += `</tr><tr>`;
                        spreads.forEach(v => histTableHtml += `<td style="padding: 4px; border: 1px solid #444; color: ${v >= 0 ? '#60a5fa' : '#ff4d4d'};">${v}</td>`);
                        histTableHtml += `</tr><tr>`;
                        bpsValues.forEach(v => histTableHtml += `<td style="padding: 4px; border: 1px solid #444; color: #ffb74d;">${v}</td>`);
                        histTableHtml += `</tr></tbody></table>`;"""
    js = js.replace(old_table_match.group(0), new_table)
else:
    print("Could not find table in analyzeSingle")

# Fix: loadAggregatedData had code that removed the detailsDiv... we should not remove it!
js = re.sub(r'// Remove single symbol details if present[\s\S]*?detailsDiv\.remove\(\);\s*\}', '', js)

with open("backend/ui/static/js/rolloverTool.js", "w") as f:
    f.write(js)
