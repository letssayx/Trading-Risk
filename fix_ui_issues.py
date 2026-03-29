import re

def fix_ui_issues():
    with open('backend/ui/static/js/script_workbench2.js', 'r') as f:
        js_content = f.read()

    # Revert PRO color back to Purple (#9B59B6)
    js_content = js_content.replace("{ key: 'pro', label: 'PRO', color: '#E88B1E' }", "{ key: 'pro', label: 'PRO', color: '#9B59B6' }")

    with open('backend/ui/static/js/script_workbench2.js', 'w') as f:
        f.write(js_content)

    with open('backend/ui/static/js/opt_analysis.js', 'r') as f:
        opt_js = f.read()

    # Fix ECharts Y-Axis for PCR & NIFTY in PCR chart
    opt_js_fixed = opt_js.replace("""
                {
                    type: 'value',
                    name: 'Price / PCR',
                    position: 'right',
                    splitLine: { lineStyle: { color: '#333', type: 'dashed' } },
                    axisLabel: { color: '#888' },
                    nameTextStyle: { color: '#888' }
                }
            ]""", """
                {
                    type: 'value',
                    name: 'Price (FUT1)',
                    position: 'right',
                    splitLine: { lineStyle: { color: '#333', type: 'dashed' } },
                    axisLabel: { color: '#888' },
                    nameTextStyle: { color: '#888' }
                },
                {
                    type: 'value',
                    name: 'PCR',
                    position: 'right',
                    offset: 60,
                    splitLine: { show: false },
                    axisLabel: { color: '#888' },
                    nameTextStyle: { color: '#888' }
                }
            ]""")

    # Change PCR series to use yAxisIndex: 2
    opt_js_fixed = opt_js_fixed.replace("""
                {
                    name: 'PCR',
                    type: 'line',
                    data: data.pcr,
                    itemStyle: { color: '#00FF00' },
                    lineStyle: { width: 2 },
                    symbol: 'none',
                    yAxisIndex: 1
                }""", """
                {
                    name: 'PCR',
                    type: 'line',
                    data: data.pcr,
                    itemStyle: { color: '#00FF00' },
                    lineStyle: { width: 2 },
                    symbol: 'none',
                    yAxisIndex: 2
                }""")

    with open('backend/ui/static/js/opt_analysis.js', 'w') as f:
        f.write(opt_js_fixed)

    with open('backend/ui/templates/workbench.html', 'r') as f:
        html_content = f.read()

    # Make lower-left table scroll properly and lower-right chart have a lookback filter
    html_fixed = html_content.replace("""
                        <!-- 4a. 500 Day Price & PCR Overlay -->
                        <div style="flex: 1; background: #1e1e1e; border: 1px solid #333; padding: 15px; border-radius: 4px; display: flex; flex-direction: column; min-height: 400px;">
                            <h3 style="margin: 0 0 10px 0; font-size: 14px; color: #ccc;">500-Day Trend: Price & PCR Overlay vs Open Interest</h3>
""", """
                        <!-- 4a. 500 Day Price & PCR Overlay -->
                        <div style="flex: 1; background: #1e1e1e; border: 1px solid #333; padding: 15px; border-radius: 4px; display: flex; flex-direction: column; min-height: 400px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                <h3 style="margin: 0; font-size: 14px; color: #ccc;">Historical Trend: Price & PCR Overlay vs Open Interest</h3>
                                <select id="opt-analysis-lookback" class="history-input" style="padding: 2px 5px;" onchange="loadOptionsAnalysis()">
                                    <option value="30">30 Days</option>
                                    <option value="60">60 Days</option>
                                    <option value="90">90 Days</option>
                                    <option value="252">252 Days</option>
                                    <option value="500" selected>500 Days</option>
                                </select>
                            </div>
""")
    with open('backend/ui/templates/workbench.html', 'w') as f:
        f.write(html_fixed)

if __name__ == '__main__':
    fix_ui_issues()
