import re

with open("backend/ui/static/js/rolloverTool.js", "r") as f:
    current_js = f.read()

with open("rollover_61fb7b8.js", "r") as f:
    old_js = f.read()

# I need to restore:
# 1. The old HTML inside #rollover-results (the charts and the old table). I'll place the single scrip details and the matrix alongside them.
# 2. `renderAggregatedView`
# 3. `updateDynamicChart`
# 4. `sortData`

# First, extract functions from old_js
def extract_func(name):
    # This is a bit brittle, but we can match function name until the next function definition at the same indent
    match = re.search(r'^\s*' + name + r':\s*function\s*\([^)]*\)\s*\{([\s\S]*?^\s*\},|[\s\S]*?\n    \},\n\n)', old_js, re.MULTILINE)
    if not match:
        match = re.search(r'^\s*' + name + r':\s*async\s*function\s*\([^)]*\)\s*\{([\s\S]*?^\s*\},|[\s\S]*?\n    \},\n\n)', old_js, re.MULTILINE)
    return match.group(0) if match else ""

renderAggregatedView = extract_func("renderAggregatedView")
updateDynamicChart = extract_func("updateDynamicChart")
sortData = extract_func("sortData")

print("Found renderAggregatedView?", bool(renderAggregatedView))
print("Found updateDynamicChart?", bool(updateDynamicChart))
print("Found sortData?", bool(sortData))


# Now construct the combined HTML block for render
# Current HTML has #rollover-results with single details and matrix container.
# We will combine them so the order is:
# 1. Single Scrip Details
# 2. Charts Area
# 3. Table Area
# 4. Matrix Table Container

# Or actually, the request asks to keep the original stuff as is. Let's just insert the single scrip details and matrix into the old html layout.

combined_html = """
                <div id="rollover-results" style="flex: 1; overflow: auto; display: flex; flex-direction: column; gap: 20px; padding-bottom: 20px;">
                    <!-- Single Scrip Details -->
                    <div id="rollover-single-details"></div>

                    <!-- Charts Area -->
                    <div style="display: flex; gap: 20px; height: 300px; flex-shrink: 0; width: 100%;">
                        <div style="flex: 1; background: #1e1e1e; border: 1px solid #333; border-radius: 4px; padding: 10px;">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
                                <div style="display:flex; gap:10px;">
                                    <select id="rollover-chart-sector-filter" class="form-control history-input" style="padding: 2px 5px;" onchange="RolloverTool.updateDynamicChart()">
                                        <option value="ALL">All Sectors Avg</option>
                                    </select>
                                    <select id="rollover-chart-stock-filter" class="form-control history-input" style="padding: 2px 5px; display:none;" onchange="RolloverTool.updateDynamicChart()">
                                        <option value="">Select Stock</option>
                                    </select>
                                </div>
                                <button class="btn btn-secondary" style="padding: 2px 6px; font-size: 10px;" onclick="if(window.rolloverDynamicChartInstance) exportChartDataToCSV(window.rolloverDynamicChartInstance, 'Dynamic_Rollover')"><i class="fas fa-download"></i> CSV</button>
                            </div>
                            <div id="rollover-dynamic-chart" style="width: 100%; height: calc(100% - 30px);"></div>
                        </div>
                    </div>

                    <!-- Matrix Table -->
                    <div style="display: flex; justify-content: flex-end; margin-bottom: -15px;">
                        <button class="btn btn-secondary" style="padding: 2px 6px; font-size: 10px; margin-right: 15px;" onclick="RolloverTool.exportMatrixCSV()"><i class="fas fa-download"></i> CSV</button>
                    </div>
                    <div id="rollover-matrix-container" class="table-wrapper" style="border: 1px solid #333; border-radius: 4px; overflow-x: auto; flex: 1; min-height: 400px; max-height: calc(100vh - 450px); overflow-y: auto;">
                    </div>

                    <!-- Table Area -->
                    <div style="display: flex; justify-content: flex-end; margin-bottom: 5px;">
                        <button class="btn btn-secondary" style="padding: 2px 6px; font-size: 10px;" onclick="exportTableToCSV('rollover-analysis-table', 'Rollover_Analysis')"><i class="fas fa-download"></i> CSV</button>
                    </div>
                    <div class="table-wrapper" style="border: 1px solid #333; border-radius: 4px; overflow-x: auto; flex: 1; min-height: 400px; max-height: calc(100vh - 450px); overflow-y: auto;">
                        <table class="data-table" id="rollover-analysis-table" style="width: 100%; table-layout: fixed;">
                            <thead style="position: sticky; top: 0; background: #222; z-index: 10;">
                                <tr>
                                    <th style="padding: 8px; width: 30px;"></th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('symbol')">Symbol ↕</th>
                                    <th style="padding: 8px;">Date</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('rollover_pct')">Rollover % ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('rollover_cost')">Spread (Pts) ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('rollover_cost_pct')">Cost % ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('fut_close')">FUT Price ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('price_chg_pct')">Price Chg % ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('total_oi')">Total OI ↕</th>
                                    <th style="padding: 8px; cursor: pointer;" onclick="RolloverTool.sortData('oi_chg_pct')">OI Chg % ↕</th>
                                </tr>
                            </thead>
                            <tbody id="rollover-analysis-body">
                                <tr><td colspan="9" style="text-align:center; color:#888;">Loading Rollover Data...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
"""

# Now replace the current HTML in current_js with the combined_html
import re
new_js = re.sub(
    r'<div id="rollover-results"[\s\S]*?</div>\s*</div>\s*</div>\s*`;',
    combined_html + '\n            </div>\n        `;',
    current_js
)

# Now we need to append the missing functions (renderAggregatedView, updateDynamicChart, sortData) back into new_js
# We can insert them right before analyzeSingle:
funcs_to_insert = f"""
{renderAggregatedView}
{updateDynamicChart}
{sortData}
"""

new_js = new_js.replace("  analyzeSingle: async function () {", funcs_to_insert + "\n  analyzeSingle: async function () {")

# Also, syncAndLoadAggregatedData and loadAggregatedData need to call renderAggregatedView() and updateDynamicChart()
# like they did in the old version!
# In old_js:
#   if (json.data && Array.isArray(json.data)) {
#      this.allData = json.data;
#      this.renderAggregatedView();
#      this.updateDynamicChart();

# In new_js, loadAggregatedData is storing allData, calling renderMatrix, but we also need it to call the old functions.
# Let's patch loadAggregatedData:
new_js = new_js.replace("this.renderMatrix(this.allData, isMoM);", "this.renderMatrix(this.allData, isMoM);\n      this.renderAggregatedView();\n      this.updateDynamicChart();")

with open("backend/ui/static/js/rolloverTool.js", "w") as f:
    f.write(new_js)
