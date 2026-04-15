import re

file_path = "backend/ui/templates/workbench.html"
with open(file_path, "r") as f:
    content = f.read()

# I think the user is just saying the Symbol Search, dropdown and expiry checkbox are not visually connected to the Historical Trend Chart, they are grouped in the header above it:
# "symbol search missing, dropdown and expiry checkbox all missing from Historical Trend Chart in OI anlaysis tab"
# Let's move them DIRECTLY into the Historical Trend Chart div so it's obvious.

chart_header_search = """                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                    <h3 style="margin: 0; font-size: 14px; color: #ccc;">Historical Trend: Price & PCR Overlay vs Open Interest</h3>
                                    <div style="display: flex; gap: 10px; align-items: center;">
                                        <label class="checkbox-label" style="font-size: 11px; margin-right: 10px; display: flex; align-items: center;"><input type="checkbox" id="pcr-expiry-only" style="margin-right: 5px;" onchange="loadOptionsAnalysis()"> Show Expiry Only</label>
                                        <button class="btn btn-secondary" style="padding: 2px 6px; font-size: 10px;" onclick="if(window.pcrChartInstance) exportChartDataToCSV(window.pcrChartInstance, 'PCR_History'); else exportChartDataToCSV(window.pcrChartInstance, 'PCR_History')"><i class="fas fa-download"></i> CSV</button>
                                        <select id="opt-analysis-lookback" class="history-input" style="padding: 2px 5px;" onchange="loadOptionsAnalysis()">"""

chart_header_replace = """                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                    <h3 style="margin: 0; font-size: 14px; color: #ccc;">Historical Trend: Price & PCR Overlay vs Open Interest</h3>
                                    <div style="display: flex; gap: 10px; align-items: center;">
                                        <input type="text" id="opt-analysis-symbol" class="history-input" placeholder="Symbol (e.g., NIFTY)" value="NIFTY" style="width: 150px; padding: 4px;" onkeydown="if(event.key==='Enter') loadOptionsAnalysis()">
                                        <label class="checkbox-label" style="font-size: 11px; margin-right: 10px; display: flex; align-items: center;"><input type="checkbox" id="pcr-expiry-only" style="margin-right: 5px;" onchange="loadOptionsAnalysis()"> Show Expiry Only</label>
                                        <select id="opt-analysis-lookback" class="history-input" style="padding: 2px 5px;" onchange="loadOptionsAnalysis()">"""

content = content.replace(chart_header_search, chart_header_replace)

old_header_search = """                        <div style="display: flex; gap: 10px; align-items: center; flex-shrink: 0; margin-top: 20px; border-top: 1px solid #333; padding-top: 20px;">
                            <h2 style="margin: 0; color: #fff; font-size: 18px;">Options Charts</h2>
                            <input type="text" id="opt-analysis-symbol" class="history-input" placeholder="Symbol (e.g., NIFTY)" value="NIFTY" style="width: 150px; padding: 4px;" onkeydown="if(event.key==='Enter') loadOptionsAnalysis()">
                            <button class="btn btn-secondary" id="btn-load-options-analysis" onclick="loadOptionsAnalysis()">Load Charts</button>
                        </div>"""

old_header_replace = """                        <div style="display: flex; gap: 10px; align-items: center; flex-shrink: 0; margin-top: 20px; border-top: 1px solid #333; padding-top: 20px;">
                            <h2 style="margin: 0; color: #fff; font-size: 18px;">Options Charts</h2>
                        </div>"""

content = content.replace(old_header_search, old_header_replace)

with open(file_path, "w") as f:
    f.write(content)
