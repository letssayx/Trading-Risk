import re

with open('backend/ui/templates/workbench.html', 'r') as f:
    content = f.read()

# Replace lot sizes
content = content.replace("document.getElementById('bb-lot')", "document.getElementById('bb-shares-calc')")
content = content.replace("document.getElementById('ofs-lot')", "document.getElementById('ofs-shares-calc')")

# Fix duplicate calculateOFSShares function
pattern = re.compile(r'// Delete the old implementation if we are replacing it\s*function calculateOFSShares\(\) {.*?}\s*</script>', re.DOTALL)
content = re.sub(pattern, '</script>', content)

# Fix labels
content = content.replace('<label style="width: 150px; display: inline-block;">Total Buy Back Offer:</label>\n                                <input type="number" id="ofs-offer"', '<label style="width: 150px; display: inline-block;">Total OFS Offer:</label>\n                                <input type="number" id="ofs-offer"')
content = content.replace('id="ofs-price" class="history-input" value="1475"', 'id="ofs-price" class="history-input" value="0"')

# Fix malformed divs
content = content.replace('<div                 <!-- SUB-TAB: PPCM (Placeholder) -->', '<!-- SUB-TAB: PPCM (Placeholder) -->')

# Add missing subtabs to Commodities
missing_bullion = """                <!-- SUB-TAB: Bullion -->
                <div id="comm-tab-bullion" class="comm-sub-tab active" style="height: 100%; width: 100%;">
                    <h2 style="color: #fff; margin-top: 0;">Bullion</h2>
                    <p style="color: #888;">Module under construction.</p>
                </div>
            </div>
        </div>"""
content = content.replace('                <div id="comm-tab-bullion" class="comm-sub-tab active" style="height: 100%; width: 100%;">\n\n        <!-- TAB CRYPTO -->', missing_bullion + '\n\n        <!-- TAB CRYPTO -->')

with open('backend/ui/templates/workbench.html', 'w') as f:
    f.write(content)

with open('backend/ui/static/js/script_workbench2.js', 'r') as f:
    content2 = f.read()

# Fix history to import lag loop
content2 = content2.replace("""
            if (tabName === 'import') {
                if (window.uploader) {
                    window.uploader.open();
                }
                return; // Prevent switching the active UI tab to 'import', which has no UI div and causes a reset loop
            }""", "")
content2 = content2.replace("window.uploader.open = () => switchMainTab('import');", "// window.uploader.open = () => switchMainTab('import');")

with open('backend/ui/static/js/script_workbench2.js', 'w') as f:
    f.write(content2)
