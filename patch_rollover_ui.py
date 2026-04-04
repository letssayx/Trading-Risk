import re

with open('backend/ui/static/js/rolloverTool.js', 'r') as f:
    content = f.read()

# Replace the HTML structure
# We need:
# 1. flex: 1, display: flex, flex-direction: column, width: 100%, height: 100% on the main container
# 2. Top section: display: flex, width: 100%
#    - Left chart: flex: 1
#    - Right chart: flex: 1
# 3. Bottom section (table): flex: 1, overflow: auto, width: 100%

# Let's extract the `render:` method's HTML string and modify it
render_start = content.find("render: function(containerId) {")
if render_start != -1:
    render_end = content.find("const input = document.getElementById('rollover-symbol');", render_start)

    new_render = """render: function(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <div style="display: flex; flex-direction: column; width: 100%; height: 100%; padding: 10px; box-sizing: border-box;">

                <!-- Header and Filters -->
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-shrink: 0;">
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <h2 style="margin: 0;">Rollover Analysis</h2>
                        <select id="rollover-sector-filter" onchange="RolloverTool.filterData()" style="padding: 5px; background: #333; color: #fff; border: 1px solid #555;">
                            <option value="">All Sectors</option>
                        </select>
                        <input type="text" id="rollover-symbol" placeholder="Search/Filter Symbol" style="padding: 5px; background: #333; color: #fff; border: 1px solid #555;">
                        <button onclick="RolloverTool.loadAggregatedData()" class="btn" style="background: #007bff; color: white; border: none; padding: 5px 10px; cursor: pointer;">Refresh All</button>
                        <button onclick="RolloverTool.analyzeSingle()" class="btn" style="background: #444; color: white; border: none; padding: 5px 10px; cursor: pointer;">Load Single Details</button>
                        <button onclick="RolloverTool.exportCSV()" class="btn" style="background: #444; color: white; border: none; padding: 5px 10px; cursor: pointer;">CSV</button>
                    </div>
                    <div id="rollover-date-display" style="color: #aaa; font-size: 0.9em;">Date: --</div>
                </div>

                <div id="rollover-results" style="display: flex; flex-direction: column; flex-grow: 1; overflow: hidden;">

                    <!-- Top Charts Row -->
                    <div style="display: flex; width: 100%; gap: 10px; margin-bottom: 15px; flex-shrink: 0; height: 350px;">

                        <!-- Left Chart: Previous 2 Expiry Sectoral Rollover -->
                        <div style="flex: 1; background: #222; border: 1px solid #333; padding: 10px; display: flex; flex-direction: column;">
                            <div style="font-weight: bold; margin-bottom: 5px; text-align: center; color: #ccc;">Previous 2 Expiries Sectoral Rollover</div>
                            <div id="rollover-sector-chart" style="flex-grow: 1; min-height: 0;"></div>
                        </div>

                        <!-- Right Chart: Current Sector / Stock History -->
                        <div style="flex: 1; background: #222; border: 1px solid #333; padding: 10px; display: flex; flex-direction: column;">
                            <div style="margin-bottom: 5px; display: flex; justify-content: center; gap: 10px;">
                                <select id="rollover-chart-sector-filter" onchange="RolloverTool.updateDynamicChart()" style="padding: 4px; background: #333; color: #fff; border: 1px solid #555;">
                                    <option value="ALL">ALL (Sectors)</option>
                                </select>
                                <select id="rollover-chart-stock-filter" onchange="RolloverTool.updateDynamicChart()" style="padding: 4px; background: #333; color: #fff; border: 1px solid #555; display: none;">
                                    <option value="">Select Stock</option>
                                </select>
                            </div>
                            <div id="rollover-dynamic-chart" style="flex-grow: 1; min-height: 0;"></div>
                        </div>
                    </div>

                    <!-- Bottom Table Section -->
                    <div style="flex-grow: 1; overflow-y: auto; background: #222; border: 1px solid #333; position: relative;">
                        <table id="rollover-analysis-table" style="width: 100%; border-collapse: collapse; text-align: left; font-size: 0.9em;">
                            <thead style="position: sticky; top: 0; background: #222; z-index: 10; box-shadow: 0 2px 2px rgba(0,0,0,0.5);">
                                <tr style="border-bottom: 1px solid #444;">
                                    <th style="padding: 10px 8px; width: 40px;"></th>
                                    <th style="padding: 10px 8px; cursor: pointer;" onclick="RolloverTool.sortData('symbol')">Symbol ↕</th>
                                    <th style="padding: 10px 8px; cursor: pointer;" onclick="RolloverTool.sortData('sector')">Sector ↕</th>
                                    <th style="padding: 10px 8px; cursor: pointer;" onclick="RolloverTool.sortData('rollover_pct')">Rollover % ↕</th>
                                    <th style="padding: 10px 8px; cursor: pointer;" onclick="RolloverTool.sortData('oi_chg_pct')">OI Change % ↕</th>
                                    <th style="padding: 10px 8px; cursor: pointer;" onclick="RolloverTool.sortData('price')">FUT Price ↕</th>
                                    <th style="padding: 10px 8px; cursor: pointer;" onclick="RolloverTool.sortData('price_chg_pct')">Price Chg % ↕</th>
                                    <th style="padding: 10px 8px; cursor: pointer;" onclick="RolloverTool.sortData('rollover_cost')">Spread (Pts) ↕</th>
                                    <th style="padding: 10px 8px; cursor: pointer;" onclick="RolloverTool.sortData('rollover_cost_pct')">Cost % ↕</th>
                                    <th style="padding: 10px 8px; cursor: pointer;" onclick="RolloverTool.sortData('near_oi')">Near OI ↕</th>
                                    <th style="padding: 10px 8px; cursor: pointer;" onclick="RolloverTool.sortData('total_oi')">Total OI ↕</th>
                                </tr>
                            </thead>
                            <tbody id="rollover-analysis-body">
                                <tr><td colspan="11" style="text-align:center; padding: 20px; color:#888;">Loading Rollover Data...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;

        """

    content = content[:render_start] + new_render + content[render_end:]

    with open('backend/ui/static/js/rolloverTool.js', 'w') as f:
        f.write(content)
    print("UI layout patched in rolloverTool.js")
