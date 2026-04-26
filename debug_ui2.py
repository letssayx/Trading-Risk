with open("backend/ui/templates/workbench.html", "r") as f:
    html = f.read()

start = html.find('<!-- TAB 1: TERMINAL (Original Workbench) -->')
end = html.find('<!-- TAB AI-ANALYZE -->')

sub = html[start:end]
b = sub.count("<div") - sub.count("</div")
print("Balance in tab terminal:", b)

start = html.find('<!-- TAB AI-ANALYZE -->')
end = html.find('<!-- TAB DERIVATIVES -->')
sub = html[start:end]
b = sub.count("<div") - sub.count("</div")
print("Balance in tab ai_analyze:", b)

start = html.find('<!-- TAB DERIVATIVES -->')
end = html.find('<!-- TAB SPECIAL SITUATION ARBITRAGE -->')
sub = html[start:end]
b = sub.count("<div") - sub.count("</div")
print("Balance in tab derivatives:", b)

start = html.find('<!-- TAB SPECIAL SITUATION ARBITRAGE -->')
end = html.find('<!-- TAB FUNDAMENTAL ANALYSIS -->')
sub = html[start:end]
b = sub.count("<div") - sub.count("</div")
print("Balance in tab special arb:", b)
