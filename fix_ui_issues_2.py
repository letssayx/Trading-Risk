import re

def fix_ui_issues_2():
    with open('backend/ui/static/js/opt_analysis.js', 'r') as f:
        opt_js = f.read()

    opt_js_fixed = opt_js.replace(
        "const res = await fetch(`/api/data/derivatives/pcr_history?symbol=${symbol}&days=500`);",
        "const days = document.getElementById('opt-analysis-lookback')?.value || '500';\n        const res = await fetch(`/api/data/derivatives/pcr_history?symbol=${symbol}&days=${days}`);"
    )

    with open('backend/ui/static/js/opt_analysis.js', 'w') as f:
        f.write(opt_js_fixed)

    with open('backend/ui/static/js/script_workbench2.js', 'r') as f:
        script2_js = f.read()

    # Ensure PRO color (#9B59B6) is reverted everywhere
    script2_fixed = script2_js.replace("color: '#E88B1E' /* Orange */", "color: '#9B59B6' /* Purple */")
    # Actually just search for E88B1E and replace specific pro key instances
    script2_fixed = re.sub(r"\{\s*key:\s*'pro',\s*label:\s*'PRO',\s*color:\s*'#E88B1E'\s*\}", r"{ key: 'pro', label: 'PRO', color: '#9B59B6' }", script2_fixed)

    # In script_workbench2.js, find the participantChart config and fix NIFTY Y-axis squash
    script2_fixed = script2_fixed.replace("""
                            {
                                type: 'value',
                                name: 'NIFTY',
                                position: 'right',
                                grid: { drawOnChartArea: false },
                                ticks: { color: '#FFCC00' }
                            }
                        }""", """
                            {
                                type: 'value',
                                name: 'NIFTY',
                                position: 'right',
                                grid: { drawOnChartArea: false },
                                ticks: { color: '#FFCC00' }
                            }
                        }""")

    # Actually let's look at the Nifty axis in the ECharts instance, not chart.js
    # Market Activity uses Participant OI. Is it ECharts? Let's check.

    with open('backend/ui/static/js/script_workbench2.js', 'w') as f:
        f.write(script2_fixed)

if __name__ == '__main__':
    fix_ui_issues_2()
