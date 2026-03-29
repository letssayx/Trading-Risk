import re

def fix_ui_issues_3():
    with open('backend/ui/static/js/script_workbench2.js', 'r') as f:
        script2_js = f.read()

    # Re-fix PRO Color #E88B1E -> #9B59B6 globally for PRO labels
    script2_fixed = script2_js.replace("{ key: 'pro', label: 'PRO', color: '#E88B1E' }", "{ key: 'pro', label: 'PRO', color: '#9B59B6' }")

    # In participantChartInstance, fix NIFTY yAxis scaling
    script2_fixed = script2_fixed.replace("""
                                { type: 'value', name: 'NIFTY', position: 'right', splitLine: { show: false }, axisLabel: { color: '#888' }, nameTextStyle: { color: '#888' } }
                            ],
                            series: [""", """
                                { type: 'value', name: 'NIFTY', position: 'right', splitLine: { show: false }, axisLabel: { color: '#888' }, nameTextStyle: { color: '#888' } }
                            ],
                            series: [""")

    # Actually wait, let's look at the NIFTY series specifically
    script2_fixed = script2_fixed.replace("""
                                {
                                    name: 'NIFTY',
                                    type: 'line',
                                    data: pData.nifty_close,
                                    itemStyle: { color: '#FFCC00' },
                                    symbol: 'none',
                                    lineStyle: { width: 2 }
                                }
                            ]
                        };""", """
                                {
                                    name: 'NIFTY',
                                    type: 'line',
                                    data: pData.nifty_close,
                                    itemStyle: { color: '#FFCC00' },
                                    symbol: 'none',
                                    lineStyle: { width: 2 },
                                    yAxisIndex: 1
                                }
                            ]
                        };""")

    with open('backend/ui/static/js/script_workbench2.js', 'w') as f:
        f.write(script2_fixed)

    with open('backend/ui/static/js/opt_analysis.js', 'r') as f:
        opt_js = f.read()

    # Fix opt_analysis lookback filter line properly using regex
    opt_js_fixed = re.sub(
        r"const res = await fetch\(`/api/data/derivatives/pcr_history\?symbol=\$\{symbol\}&days=500`\);",
        "const days = document.getElementById('opt-analysis-lookback')?.value || '500';\n        const res = await fetch(`/api/data/derivatives/pcr_history?symbol=${symbol}&days=${days}`);",
        opt_js
    )
    with open('backend/ui/static/js/opt_analysis.js', 'w') as f:
        f.write(opt_js_fixed)

if __name__ == '__main__':
    fix_ui_issues_3()
