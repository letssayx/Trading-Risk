with open("backend/ui/templates/workbench.html", "r") as f:
    content = f.read()

search_text = """                    <div style="display: flex; gap: 15px; margin-bottom: 20px; align-items: center; background: #1e1e1e; padding: 15px; border-radius: 4px; border: 1px solid #333;">
                        <input type="text" id="vol-analysis-symbol" class="history-input" value="NIFTY" style="width: 150px;" placeholder="Symbol">
                        <select id="vol-analysis-expiry-type" class="history-input" >
                            <option value="monthly">Monthly Expiry</option>
                            <option value="weekly">Weekly Expiry</option>
                        </select>
                        <label style="color: #ccc; margin: 0; font-size: 14px;">Lookback Period:</label>
                        <select id="vol-analysis-lookback" class="history-input" >
                            <option value="5">5 Days</option>
                            <option value="30">30 Days</option>
                            <option value="60">60 Days</option>
                            <option value="90">90 Days</option>
                            <option value="252">252 Days</option>
                            <option value="500" selected>500 Days</option>
                        </select>
                        <select id="vol-analysis-box-days" class="history-input" >
                            <option value="3">3 DTE</option>
                            <option value="7" selected>7 DTE</option>
                            <option value="10">10 DTE</option>
                            <option value="15">15 DTE</option>
                            <option value="20">20 DTE</option>
                            <option value="30">30 DTE</option>
                        </select>
                        <button class="btn btn-primary" onclick="loadVolatilityAnalysis()">Load</button>
                        <span style="color: #888; font-size: 11px; margin-left: auto;">*DTE - Days to Expiry</span>
                    </div>

                    <!-- Chart 1: Pre-Expiry Price Action -->
                    <div style="width: 100%; height: 600px; background: #1e1e1e; border: 1px solid #333; padding: 10px; border-radius: 4px; margin-bottom: 20px;">
                        <div style="display:flex; justify-content:flex-end; margin-bottom:10px;">
                            <button class="btn btn-secondary" onclick="if(window.volPreExpiryChart) exportChartDataToCSV(window.volPreExpiryChart, 'Vol_Pre_Expiry'); else exportChartDataToCSV(volPreExpiryChart, 'Vol_Pre_Expiry')"><i class="fas fa-download"></i> CSV</button>
                        </div>
                        <div id="vol-pre-expiry-chart" style="width: 100%; height: calc(100% - 35px);"></div>
                    </div>

                    <!-- Chart 2: Volatility Cone -->
                    <div style="width: 100%; height: 600px; background: #1e1e1e; border: 1px solid #333; padding: 10px; border-radius: 4px; margin-bottom: 20px;">
                        <div style="display:flex; justify-content:flex-end; margin-bottom:10px; align-items: center; gap: 10px;">
                            <label style="color: #ccc; font-size: 11px;"><input type="checkbox" id="vol-analysis-force-calc" style="margin-right: 5px;"> Force Recalculate History</label>
                            <button class="btn btn-secondary" onclick="if(window.volConeChart) exportChartDataToCSV(window.volConeChart, 'Volatility_Cone'); else exportChartDataToCSV(volConeChart, 'Volatility_Cone')"><i class="fas fa-download"></i> CSV</button>
                        </div>"""

replace_text = """                    <div style="display: flex; gap: 15px; margin-bottom: 20px; align-items: center; background: #1e1e1e; padding: 15px; border-radius: 4px; border: 1px solid #333;">
                        <input type="text" id="vol-analysis-symbol" class="history-input" value="NIFTY" style="width: 150px;" placeholder="Symbol">
                        <select id="vol-analysis-expiry-type" class="history-input" >
                            <option value="monthly">Monthly Expiry</option>
                            <option value="weekly">Weekly Expiry</option>
                        </select>
                        <label style="color: #ccc; margin: 0; font-size: 14px;">Lookback Period:</label>
                        <select id="vol-analysis-lookback" class="history-input" >
                            <option value="5">5 Days</option>
                            <option value="30">30 Days</option>
                            <option value="60">60 Days</option>
                            <option value="90">90 Days</option>
                            <option value="252">252 Days</option>
                            <option value="500" selected>500 Days</option>
                        </select>
                        <button class="btn btn-primary" onclick="loadVolatilityAnalysis()">Load</button>
                    </div>

                    <!-- Chart 1: Pre-Expiry Price Action -->
                    <div style="width: 100%; height: 600px; background: #1e1e1e; border: 1px solid #333; padding: 10px; border-radius: 4px; margin-bottom: 20px;">
                        <div style="display:flex; justify-content: space-between; margin-bottom:10px; align-items: center;">
                            <div style="display:flex; gap: 10px; align-items: center;">
                                <label style="color: #ccc; margin: 0; font-size: 12px;">Pre-Expiry Window (DTE):</label>
                                <select id="vol-analysis-box-days" class="history-input" style="padding: 4px;" onchange="loadVolatilityAnalysis()">
                                    <option value="3">3 DTE</option>
                                    <option value="7" selected>7 DTE</option>
                                    <option value="10">10 DTE</option>
                                    <option value="15">15 DTE</option>
                                    <option value="20">20 DTE</option>
                                    <option value="30">30 DTE</option>
                                </select>
                            </div>
                            <button class="btn btn-secondary" onclick="if(window.volPreExpiryChart) exportChartDataToCSV(window.volPreExpiryChart, 'Vol_Pre_Expiry'); else exportChartDataToCSV(volPreExpiryChart, 'Vol_Pre_Expiry')"><i class="fas fa-download"></i> CSV</button>
                        </div>
                        <div id="vol-pre-expiry-chart" style="width: 100%; height: calc(100% - 35px);"></div>
                    </div>

                    <!-- Chart 2: Volatility Cone -->
                    <div style="width: 100%; height: 600px; background: #1e1e1e; border: 1px solid #333; padding: 10px; border-radius: 4px; margin-bottom: 20px;">
                        <div style="display:flex; justify-content: space-between; margin-bottom:10px; align-items: center;">
                            <div style="display:flex; gap: 10px; align-items: center;">
                                <button class="btn btn-primary" onclick="loadVolatilityAnalysis()">Run Historical IV Calculation</button>
                                <label style="color: #ccc; font-size: 11px; display: flex; align-items: center;"><input type="checkbox" id="vol-analysis-force-calc" style="margin-right: 5px;"> Force Recalculate History</label>
                            </div>
                            <button class="btn btn-secondary" onclick="if(window.volConeChart) exportChartDataToCSV(window.volConeChart, 'Volatility_Cone'); else exportChartDataToCSV(volConeChart, 'Volatility_Cone')"><i class="fas fa-download"></i> CSV</button>
                        </div>"""

if search_text in content:
    content = content.replace(search_text, replace_text)
    with open("backend/ui/templates/workbench.html", "w") as f:
        f.write(content)
    print("Replaced successfully")
else:
    print("Not found")
