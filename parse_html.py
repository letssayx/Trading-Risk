with open('backend/ui/templates/workbench.html', 'r') as f:
    lines = f.readlines()

new_lines = []
in_snapshot_block = False
snapshot_header_lines = []

for i, line in enumerate(lines):
    if "if (snapshotMode) {" in line and "thead.innerHTML =" in lines[i+1]:
        in_snapshot_block = True
        new_lines.append(line)
        continue

    if in_snapshot_block:
        if "const renderChunk = (start) => {" in line:
            in_snapshot_block = False
            # We found the end of the snapshot block.
            # Let's insert the `} else { thead.innerHTML = ... }`

            # The current snapshot header block does NOT include Date and Symbol for timeseries!
            # Wait, let's look at what the current code has.
            pass
