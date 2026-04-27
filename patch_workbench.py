import re

with open('backend/ui/templates/workbench.html', 'r') as f:
    content = f.read()

# Replace lot sizes
content = content.replace("document.getElementById('bb-lot')", "document.getElementById('bb-shares-calc')")
content = content.replace("document.getElementById('ofs-lot')", "document.getElementById('ofs-shares-calc')")

# Fix duplicate calculateOFSShares function
pattern = re.compile(r'// Delete the old implementation if we are replacing it[\s\S]*?}\s*}\s*</script>', re.MULTILINE)
content = re.sub(pattern, '</script>', content)

# Fix labels
content = content.replace('<label style="width: 150px; display: inline-block;">Total Buy Back Offer:</label>\n                                <input type="number" id="ofs-offer"', '<label style="width: 150px; display: inline-block;">Total OFS Offer:</label>\n                                <input type="number" id="ofs-offer"')
content = content.replace('id="ofs-price" class="history-input" value="1475"', 'id="ofs-price" class="history-input" value="0"')

# Fix malformed divs
content = content.replace('<div                 <!-- SUB-TAB: PPCM (Placeholder) -->', '<!-- SUB-TAB: PPCM (Placeholder) -->')

with open('backend/ui/templates/workbench.html', 'w') as f:
    f.write(content)
