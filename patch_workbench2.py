with open("backend/ui/templates/workbench.html", "r") as f:
    content = f.read()

old_canvas = """                            <div style="display: flex; justify-content: space-between; align-items: baseline;">
                                <h3 style="margin: 0 0 10px 0; font-size: 14px; color: #ccc;">Participant OI Trend</h3>
                                <span id="participant-oi-summary" style="font-size: 12px; color: #aaa;"></span>
                            </div>
                            <canvas id="participantOiChart"></canvas>"""

new_canvas = """                            <div style="display: flex; justify-content: space-between; align-items: baseline; position: absolute; width: calc(100% - 30px); z-index: 10;">
                                <h3 style="margin: 0 0 10px 0; font-size: 14px; color: #ccc;">FII OI Trend</h3>
                                <span id="participant-oi-summary" style="font-size: 12px; color: #aaa;"></span>
                            </div>
                            <div style="width: 100%; height: 100%; padding-top: 25px; box-sizing: border-box;">
                                <canvas id="participantOiChart"></canvas>
                            </div>"""
content = content.replace(old_canvas, new_canvas)

with open("backend/ui/templates/workbench.html", "w") as f:
    f.write(content)
