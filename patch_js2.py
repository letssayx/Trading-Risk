with open('backend/ui/templates/workbench.html', 'r') as f:
    content = f.read()

count_th_false = content.split('} else {')[1].split('const renderChunk')[0].count('<th')
print(f"Timeseries Mode TH count: {count_th_false}")
