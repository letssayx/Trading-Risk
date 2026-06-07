import re

filepath = 'backend/ui/templates/workbench.html'
with open(filepath, 'r') as f:
    content = f.read()

# Fix the trend chart header in OI Analysis which was mangled
search = """                                    <h3 style="margin: 0; font-size: 12px; color: #ccc; margin-right: 5px;">Trend: Price & PCR vs OI</h3>
            <div class="card-body">
                <div style="display: flex; justify-content: flex-end; gap: 15px; margin-bottom: 10px;">
                    <label style="color: white; font-size: 0.9em; display: flex; align-items: center; gap: 5px;">
                        <input type="checkbox" id="fii-trend-comb-oi-chk" onchange="loadFiiTrendChart()"> Comb. OI
                    </label>
                </div>
                <div id="fii-trend-chart" style="height: 400px; width: 100%;"></div>
            </div>"""

replace = """                                    <h3 style="margin: 0; font-size: 12px; color: #ccc; margin-right: 5px;">Trend: Price & PCR vs OI</h3>
                                    <label style="color: white; font-size: 0.9em; display: flex; align-items: center; gap: 5px; cursor: pointer; margin-bottom: 0;">
                                        <input type="checkbox" id="oi-trend-comb-chk" onchange="loadOiAnalysisChart()"> Comb. OI
                                    </label>
                                </div>
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <select id="oi-analysis-days" class="data-dropdown" onchange="loadOiAnalysisChart()">
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
                            <div style="flex-grow: 1; min-height: 0; position: relative;">
                                <div id="oi-trend-chart" style="position: absolute; top: 0; left: 0; right: 0; bottom: 0;"></div>
                            </div>
                        </div>"""

if search in content:
    content = content.replace(search, replace)
    with open(filepath, 'w') as f:
        f.write(content)
    print("Workbench patched")
else:
    print("Could not find block in workbench")
