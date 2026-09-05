with open("backend/ui/templates/workbench.html", "r") as f:
    content = f.read()

content = content.replace(
    '<button class="btn btn-secondary" onclick="if(typeof loadFiiAnalysis === \'function\') loadFiiAnalysis()"><i class="fas fa-sync"></i> Refresh FII Data</button>',
    '<button class="btn btn-primary" id="btn-load-fii" onclick="if(typeof loadFiiAnalysis === \'function\') loadFiiAnalysis(event)"><i class="fas fa-sync"></i> Refresh FII Data</button>'
)

with open("backend/ui/templates/workbench.html", "w") as f:
    f.write(content)
