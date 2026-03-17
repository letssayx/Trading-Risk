import re

with open('script_workbench2.js', 'r') as f:
    content = f.read()

# Add JS variables and TD for delivery and volume
old_js = """                            const eqClose = (row.eq_close_price != null && !isNaN(Number(row.eq_close_price))) ? Number(row.eq_close_price).toFixed(2) : '-';
                            const vwap = (row.vwap != null && !isNaN(Number(row.vwap))) ? Number(row.vwap).toFixed(2) : '-';
                            const fVol = (row.futures_total_vol != null && !isNaN(Number(row.futures_total_vol))) ? Number(row.futures_total_vol).toLocaleString() : '-';"""

new_js = """                            const eqClose = (row.eq_close_price != null && !isNaN(Number(row.eq_close_price))) ? Number(row.eq_close_price).toFixed(2) : '-';
                            const vwap = (row.vwap != null && !isNaN(Number(row.vwap))) ? Number(row.vwap).toFixed(2) : '-';
                            const eqVol = (row.total_eq_volume != null && !isNaN(Number(row.total_eq_volume))) ? Number(row.total_eq_volume).toLocaleString() : '-';
                            const delPct = (row.delivery_pct != null && !isNaN(Number(row.delivery_pct))) ? Number(row.delivery_pct).toFixed(2) : '-';
                            const fVol = (row.futures_total_vol != null && !isNaN(Number(row.futures_total_vol))) ? Number(row.futures_total_vol).toLocaleString() : '-';"""

content = content.replace(old_js, new_js)

old_td = """                                <td>${nearFutClose}</td>
                                <td>${eqClose}</td>
                                <td>${vwap}</td>
                                <td>${fVol}</td>"""

new_td = """                                <td>${nearFutClose}</td>
                                <td>${eqClose}</td>
                                <td>${vwap}</td>
                                <td>${eqVol}</td>
                                <td>${delPct}%</td>
                                <td>${fVol}</td>"""

content = content.replace(old_td, new_td)

with open('script_workbench2.js', 'w') as f:
    f.write(content)
print("Done script")
