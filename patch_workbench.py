with open('backend/ui/templates/workbench.html', 'r') as f:
    content = f.read()

content = content.replace('<h3 style="margin: 0 0 10px 0; font-size: 14px; color: #ccc;">FII OI Trend</h3>',
'<div style="display: flex; align-items: center;"><h3 style="margin: 0 0 10px 0; font-size: 14px; color: #ccc;">Participant OI Trend</h3><select id="participant-type-select" onchange="loadMarketActivity()" style="background: #333; color: #fff; border: 1px solid #444; border-radius: 4px; padding: 2px 5px; font-size: 12px; margin-left: 10px; margin-bottom: 10px;"><option value="FII">FII</option><option value="DII">DII</option><option value="PRO">PRO</option><option value="Client">Client</option></select></div>')

with open('backend/ui/templates/workbench.html', 'w') as f:
    f.write(content)
