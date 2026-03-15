with open('./backend/ui/templates/workbench.html', 'r') as f:
    lines = f.readlines()

def parse_th(lines):
    import re
    th_list = []
    for line in lines:
        if '<th' in line and '</th>' in line:
            # strip out tags to get text
            text = re.sub('<[^<]+>', '', line).strip()
            th_list.append(text)
    return th_list

thead_snapshot = []
in_snap = False
for line in lines[463:508]:
    thead_snapshot.append(line)

thead_ts = []
for line in lines[853:900]:
    thead_ts.append(line)

snap_cols = parse_th(thead_snapshot)
ts_cols = parse_th(thead_ts)
print("Snap count:", len(snap_cols))
print("TS count:", len(ts_cols))

for c in snap_cols:
    if c not in ts_cols:
        print("Missing in TS:", c)
for c in ts_cols:
    if c not in snap_cols:
        print("Missing in Snap:", c)
