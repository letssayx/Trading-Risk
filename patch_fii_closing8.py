import re

filepath = 'backend/ui/templates/workbench.html'
with open(filepath, 'r') as f:
    content = f.read()

# Make sure the tab wrapper for FII doesn't leak into the global layout

search = """                                <tbody>
                                    <tr><td colspan="9" style="text-align:center; color:#888;">Loading history...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- SUB-TAB MWPL Analysis -->"""

replace = """                                <tbody>
                                    <tr><td colspan="9" style="text-align:center; color:#888;">Loading history...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- SUB-TAB MWPL Analysis -->"""

# actually, the leak might not be in the FII tab. Let's look for missing divs in the trend chart replace block we did earlier.

search2 = """                            <div style="flex-grow: 1; min-height: 0; position: relative;">
                                <div id="oi-trend-chart" style="position: absolute; top: 0; left: 0; right: 0; bottom: 0;"></div>
                            </div>
                        </div>
                                    <div class="autocomplete-wrapper" style="margin-left: 10px;">"""

replace2 = """                            <div style="flex-grow: 1; min-height: 0; position: relative;">
                                <div id="oi-trend-chart" style="position: absolute; top: 0; left: 0; right: 0; bottom: 0;"></div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- SUB-TAB FII Analysis -->
                <div id="deriv-tab-fii" class="deriv-sub-tab" style="height: 100%; width: 100%; overflow-y: auto; box-sizing: border-box; display: flex; flex-direction: column; position: relative;">
                    <div style="display: flex; gap: 10px; align-items: center; margin-bottom: 0px; flex-shrink: 0; position: sticky; top: 0; z-index: 100; background: #1e1e1e; padding: 15px 20px; border-bottom: 1px solid #333;">
                        <select id="fii-analysis-days" class="history-input" style="width: 100px;" onchange="if(typeof loadFiiAnalysis === 'function') loadFiiAnalysis()">
                            <option value="5">5 Days</option>
                            <option value="7">7 Days</option>
                            <option value="30" selected>30 Days</option>
                            <option value="60">60 Days</option>
                            <option value="90">90 Days</option>
                            <option value="180">180 Days</option>
                            <option value="252">252 Days</option>
                            <option value="500">500 Days</option>
                        </select>
                        <button class="btn btn-secondary" onclick="if(typeof loadFiiAnalysis === 'function') loadFiiAnalysis()"><i class="fas fa-sync"></i> Refresh</button>
                    </div>

                    <div style="display: block; margin-bottom: 0px; padding: 20px;">
                        <!-- FII/DII Cash Flow -->
                        <div style="height: 450px; min-height: 450px; flex-shrink: 0; background: #1e1e1e; border: 1px solid #333; padding: 15px; border-radius: 4px; display: flex; flex-direction: column; margin-bottom: 20px;">
                            <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 10px;">
                                <h3 style="margin: 0; font-size: 14px; color: #ccc;">FII/DII Institutional Flows (Cash)</h3>
                                <button class="btn btn-secondary" style="padding: 2px 6px; font-size: 10px;" onclick="if(window.fiiDiiTabChartInstance) exportChartDataToCSV(window.fiiDiiTabChartInstance, 'FII_DII_Net_Pos');"><i class="fas fa-download"></i> CSV</button>
                            </div>
                            <div style="flex: 1; min-width: 0; height: 100%;">
                                <canvas id="fiiDiiTabChart"></canvas>
                            </div>
                        </div>

                        <!-- FII Trend Chart Section -->
                        <div class="card" style="margin-bottom: 10px;">
                            <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
                                <h2 style="margin: 0; font-size: 1.1em; color: white;">Trend: Price & PCR vs OI</h2>
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <div class="autocomplete-wrapper" style="margin-left: 10px;">"""

if search2 in content:
    content = content.replace(search2, replace2)
    print("Fixed missing divs and headers in FII tab logic")

# Then we remove the duplicate wrappers at the bottom
search3 = """                <!-- SUB-TAB FII Analysis -->
                <div id="deriv-tab-fii" class="deriv-sub-tab" style="height: 100%; width: 100%; overflow-y: auto; box-sizing: border-box; display: flex; flex-direction: column; position: relative;">
                    <div style="display: flex; gap: 10px; align-items: center; margin-bottom: 0px; flex-shrink: 0; position: sticky; top: 0; z-index: 100; background: #1e1e1e; padding: 15px 20px; border-bottom: 1px solid #333;">
                        <select id="fii-analysis-days" class="history-input" style="width: 100px;" onchange="if(typeof loadFiiAnalysis === 'function') loadFiiAnalysis()">
                            <option value="5">5 Days</option>
                            <option value="7">7 Days</option>
                            <option value="30" selected>30 Days</option>
                            <option value="60">60 Days</option>
                            <option value="90">90 Days</option>
                            <option value="180">180 Days</option>
                            <option value="252">252 Days</option>
                            <option value="500">500 Days</option>
                        </select>
                        <button class="btn btn-secondary" onclick="if(typeof loadFiiAnalysis === 'function') loadFiiAnalysis()"><i class="fas fa-sync"></i> Refresh</button>
                    </div>

                    <div style="display: block; margin-bottom: 0px; padding: 20px;">
                        <!-- FII/DII Cash Flow -->
                        <div style="height: 450px; min-height: 450px; flex-shrink: 0; background: #1e1e1e; border: 1px solid #333; padding: 15px; border-radius: 4px; display: flex; flex-direction: column; margin-bottom: 20px;">
                            <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 10px;">
                                <h3 style="margin: 0; font-size: 14px; color: #ccc;">FII/DII Institutional Flows (Cash)</h3>
                                <button class="btn btn-secondary" style="padding: 2px 6px; font-size: 10px;" onclick="if(window.fiiDiiTabChartInstance) exportChartDataToCSV(window.fiiDiiTabChartInstance, 'FII_DII_Net_Pos');"><i class="fas fa-download"></i> CSV</button>
                            </div>
                            <div style="flex: 1; min-width: 0; height: 100%;">
                                <canvas id="fiiDiiTabChart"></canvas>
                            </div>
                        </div>

                        <!-- FII Trend Chart Section -->
                        <div class="card" style="margin-bottom: 10px;">
                            <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
                                <h2 style="margin: 0; font-size: 1.1em; color: white;">Trend: Price & PCR vs OI</h2>
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <div class="autocomplete-wrapper" style="margin-left: 10px;">
                                        <input type="text" id="fii-analysis-index-symbol" class="history-input" style="width: 120px; padding: 4px; font-size: 11px; font-weight: bold; text-align: center; color: #fff; background: #333;" value="NIFTY" placeholder="Enter Symbol (e.g. NIFTY)" onkeydown="if(event.key === 'Enter' && typeof loadFiiTrendChart === 'function') loadFiiTrendChart()">
                                    </div>"""

replace3 = """                                    <div class="autocomplete-wrapper" style="margin-left: 10px;">
                                        <input type="text" id="fii-analysis-index-symbol" class="history-input" style="width: 120px; padding: 4px; font-size: 11px; font-weight: bold; text-align: center; color: #fff; background: #333;" value="NIFTY" placeholder="Enter Symbol (e.g. NIFTY)" onkeydown="if(event.key === 'Enter' && typeof loadFiiTrendChart === 'function') loadFiiTrendChart()">
                                    </div>"""

if search3 in content:
    content = content.replace(search3, replace3)
    print("Fixed duplicate FII tab logic")
else:
    print("No duplicate logic found.")

with open(filepath, 'w') as f:
    f.write(content)
