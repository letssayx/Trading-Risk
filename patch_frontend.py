import sys

with open('backend/ui/static/js/rolloverTool.js', 'r') as f:
    content = f.read()

# 1. 24-Month Text Search and Replace
content = content.replace("12-month history", "24-month history")
content = content.replace("12-Month Rollover History", "24-Month Rollover History")
content = content.replace("Loading 12M History", "Loading 24M History")
content = content.replace("12 Month History", "24 Month History")

# 2. Add CSV Export to Single Symbol Details
search_csv = """                <h4 style="margin-top: 20px; color: #fff;">24-Month Rollover History</h4>
                <div id="rollover-mom-history-chart" style="width: 100%; height: 250px; margin-top: 10px;"></div>"""

replace_csv = """                <div style="display: flex; justify-content: space-between; align-items: baseline; margin-top: 20px;">
                    <h4 style="margin: 0; color: #fff;" id="single-symbol-history-title">24-Month Rollover History</h4>
                    <button class="btn btn-secondary" style="padding: 2px 6px; font-size: 10px;" onclick="if(window.rolloverMomChartInstance) exportChartDataToCSV(window.rolloverMomChartInstance, 'Rollover_History_${symbol}');"><i class="fas fa-download"></i> CSV</button>
                </div>
                <div id="rollover-mom-history-chart" style="width: 100%; height: 250px; margin-top: 10px;"></div>"""

content = content.replace(search_csv, replace_csv)

# 3. Add Top Bar Search Clear Button & Layout
search_layout = """                    <div style="position: relative;">
                        <input type="text" id="rollover-symbol" class="form-control history-input" placeholder="Search/Filter Symbol" style="width: 150px; padding: 4px; padding-right: 20px;" oninput="RolloverTool.filterData()">
                        <span id="rollover-clear-search" style="position: absolute; right: 5px; top: 50%; transform: translateY(-50%); cursor: pointer; color: #888; display: none;" onclick="document.getElementById('rollover-symbol').value=''; RolloverTool.filterData(); RolloverTool.loadAggregatedData(); this.style.display='none';">✖</span>
                    </div>

                    <button onclick="RolloverTool.analyzeSingle()" class="btn btn-secondary">Load Single Details</button>

                    <label style="color:#ccc; font-size:12px; margin-left: 10px;"><input type="checkbox" id="rollover-force-refresh"> Force</label>
                    <button id="rollover-refresh-btn" onclick="RolloverTool.syncAndLoadAggregatedData()" class="btn btn-primary"><i class="fas fa-sync"></i> Refresh All</button>


                    <div style="display: flex; gap: 10px; align-items: center; margin-left: 20px; border-left: 1px solid #444; padding-left: 15px;">
                        <span style="color: #aaa; font-size: 13px;">History Range:</span>
                        <label style="color: #fff; display: flex; align-items: center; gap: 5px; font-size: 13px;">
                            <input type="radio" name="rollover_days" value="7" onchange="RolloverTool.loadAggregatedData()"> 7 Days
                        </label>
                        <label style="color: #fff; display: flex; align-items: center; gap: 5px; font-size: 13px;">
                            <input type="radio" name="rollover_days" value="14" checked onchange="RolloverTool.loadAggregatedData()"> 14 Days
                        </label>
                        <label style="color: #fff; display: flex; align-items: center; gap: 5px; font-size: 13px;">
                            <input type="radio" name="rollover_days" value="30" onchange="RolloverTool.loadAggregatedData()"> 30 Days
                        </label>
                    </div>

                    <div style="display: flex; gap: 10px; align-items: center; margin-left: 20px; border-left: 1px solid #444; padding-left: 15px;">
                        <label style="color: #fff; display: flex; align-items: center; gap: 5px; font-size: 13px;" title="Show Month-on-Month expiry rollover instead of daily progression">
                            <input type="checkbox" id="rollover-mom-checkbox" checked onchange="RolloverTool.loadAggregatedData(); if(document.getElementById('rollover-symbol').value) { RolloverTool.analyzeSingle(); }"> Month-on-Month
                        </label>
                    </div>"""

replace_layout = """                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div style="position: relative;">
                            <input type="text" id="rollover-symbol" class="form-control history-input" placeholder="Search/Filter Symbol" style="width: 150px; padding: 4px; padding-right: 20px;" oninput="RolloverTool.filterData()">
                            <span id="rollover-clear-search" style="position: absolute; right: 5px; top: 50%; transform: translateY(-50%); cursor: pointer; color: #888; display: none;" onclick="document.getElementById('rollover-symbol').value=''; RolloverTool.filterData(); RolloverTool.loadAggregatedData(); this.style.display='none';">✖</span>
                        </div>
                        <button onclick="RolloverTool.analyzeSingle()" class="btn btn-secondary">Load Single Details</button>
                    </div>

                    <div style="display: flex; gap: 10px; align-items: center; margin-left: 20px; border-left: 1px solid #444; padding-left: 15px;">
                        <label style="color: #fff; display: flex; align-items: center; gap: 5px; font-size: 13px;" title="Show Month-on-Month expiry rollover instead of daily progression">
                            <input type="checkbox" id="rollover-mom-checkbox" checked onchange="RolloverTool.loadAggregatedData(); if(document.getElementById('rollover-symbol').value) { RolloverTool.analyzeSingle(); }"> Month-on-Month
                        </label>
                    </div>

                    <div style="display: flex; gap: 10px; align-items: center; margin-left: 20px; border-left: 1px solid #444; padding-left: 15px;">
                        <span style="color: #aaa; font-size: 13px;">History Range:</span>
                        <label style="color: #fff; display: flex; align-items: center; gap: 5px; font-size: 13px;">
                            <input type="radio" name="rollover_days" value="7" onchange="RolloverTool.loadAggregatedData()"> 7 Days
                        </label>
                        <label style="color: #fff; display: flex; align-items: center; gap: 5px; font-size: 13px;">
                            <input type="radio" name="rollover_days" value="14" checked onchange="RolloverTool.loadAggregatedData()"> 14 Days
                        </label>
                        <label style="color: #fff; display: flex; align-items: center; gap: 5px; font-size: 13px;">
                            <input type="radio" name="rollover_days" value="30" onchange="RolloverTool.loadAggregatedData()"> 30 Days
                        </label>
                    </div>

                    <div style="display: flex; gap: 10px; align-items: center; margin-left: auto;">
                        <label style="color:#ccc; font-size:12px;"><input type="checkbox" id="rollover-force-refresh"> Force</label>
                        <button id="rollover-refresh-btn" onclick="RolloverTool.syncAndLoadAggregatedData()" class="btn btn-primary"><i class="fas fa-sync"></i> Refresh All</button>
                    </div>"""

content = content.replace(search_layout, replace_layout)

with open('backend/ui/static/js/rolloverTool.js', 'w') as f:
    f.write(content)

print("Frontend patched")
