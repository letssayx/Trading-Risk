import os

def test_fii_granular_embed():
    # Verify the JS logic was added to embed the granular data
    with open("backend/ui/static/js/fiiTool.js", "r") as f:
        js_content = f.read()

    # Check if granular data is correctly passed in
    assert "renderFiiSmartMoneyHistoryTable(partData, granularData);" in js_content
    # Check if getRatio was added
    assert "const getRatio = (long, short) => {" in js_content
    # Check if granular cells are mapped
    assert "granular.buy_contracts" in js_content
    assert "granular.sell_contracts" in js_content

def test_fii_html_headers_updated():
    with open("backend/ui/templates/workbench.html", "r") as f:
        html_content = f.read()

    assert "FII (Lots / Contracts)" in html_content
    # Ensure they were removed
    assert "Buy Cont." not in html_content
    assert "Sell Cont." not in html_content
    assert "Net Cont." not in html_content
