import os

def test_fii_position_removed():
    # Verify the HTML table was removed
    with open("backend/ui/templates/workbench.html", "r") as f:
        html_content = f.read()
    assert "id=\"fii-position-history-table\"" not in html_content
    assert "FII Position (Contracts and Money)" not in html_content

    # Verify the JS function was removed
    with open("backend/ui/static/js/fiiTool.js", "r") as f:
        js_content = f.read()
    assert "function renderFiiPositionHistoryTable" not in js_content

def test_pcr_chart_css_squish_fix():
    # Verify the CSS wrapper was fixed to flex-direction: column and given a min-height
    with open("backend/ui/templates/workbench.html", "r") as f:
        html_content = f.read()
    assert "height: 450px; min-height: 450px;" in html_content
    assert "display: flex; flex-direction: column;" in html_content
