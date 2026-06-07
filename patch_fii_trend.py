import re

filepath = 'backend/ui/templates/workbench.html'
with open(filepath, 'r') as f:
    content = f.read()

# Fix FII trend chart
search = """                    <!-- FII Trend Chart Section -->
                    <div class="card" style="margin-bottom: 20px;">
                        <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
                            <h2 style="margin: 0; font-size: 1.1em; color: white;">Trend: Price & PCR vs OI</h2>
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <label style="color: #aaa; font-size: 0.9em; display: flex; align-items: center; gap: 5px;">
                                    <input type="checkbox" id="fii-opt-expiry-only" onchange="loadFiiTrendChart()"> Expiry Only
                                </label>
                                <select id="fii-analysis-days" class="data-dropdown" onchange="loadFiiTrendChart()">
                                    <option value="7">7 Days</option>
                                    <option value="14">14 Days</option>
                                    <option value="30" selected>30 Days</option>
                                    <option value="60">60 Days</option>
                                    <option value="90">90 Days</option>
                                    <option value="180">180 Days</option>
                                    <option value="365">1 Year</option>
                                    <option value="500">2 Years</option>
                                </select>
                            </div>
                        </div>
                        <div class="card-body">
                            <div id="fii-trend-chart" style="height: 400px; width: 100%;"></div>
                        </div>
                    </div>"""

replace = """                    <!-- FII Trend Chart Section -->
                    <div class="card" style="margin-bottom: 10px;">
                        <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
                            <h2 style="margin: 0; font-size: 1.1em; color: white;">Trend: Price & PCR vs OI</h2>
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <label style="color: white; font-size: 0.9em; display: flex; align-items: center; gap: 5px;">
                                    <input type="checkbox" id="fii-trend-comb-oi-chk" onchange="loadFiiTrendChart()"> Comb. OI
                                </label>
                                <label style="color: #aaa; font-size: 0.9em; display: flex; align-items: center; gap: 5px;">
                                    <input type="checkbox" id="fii-opt-expiry-only" onchange="loadFiiTrendChart()"> Expiry Only
                                </label>
                                <select id="fii-analysis-days" class="data-dropdown" onchange="loadFiiTrendChart()">
                                    <option value="7">7 Days</option>
                                    <option value="14">14 Days</option>
                                    <option value="30" selected>30 Days</option>
                                    <option value="60">60 Days</option>
                                    <option value="90">90 Days</option>
                                    <option value="180">180 Days</option>
                                    <option value="365">1 Year</option>
                                    <option value="500">2 Years</option>
                                </select>
                            </div>
                        </div>
                        <div class="card-body">
                            <div id="fii-trend-chart" style="height: 400px; width: 100%;"></div>
                        </div>
                    </div>"""

if search in content:
    content = content.replace(search, replace)
    with open(filepath, 'w') as f:
        f.write(content)
    print("Workbench patched FII trend chart")
else:
    print("Could not find block for FII trend chart in workbench")
