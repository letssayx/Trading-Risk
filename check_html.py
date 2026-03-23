from bs4 import BeautifulSoup

with open('backend/ui/templates/workbench.html', 'r') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')
mwpl = soup.find(id='deriv-tab-mwpl')
if mwpl:
    parents = [p.get('id') for p in mwpl.parents if p.get('id')]
    print("Parents of MWPL tab:", parents)
else:
    print("MWPL tab not found")

marketwatch = soup.find(id='tab-marketwatch')
if marketwatch:
    print("Marketwatch next siblings:", [s.get('id') for s in marketwatch.find_next_siblings() if s and isinstance(s, type(marketwatch)) and s.get('id')])
