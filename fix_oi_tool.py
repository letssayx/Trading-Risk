import re

file_path = "backend/ui/static/js/oiTool.js"
with open(file_path, "r") as f:
    content = f.read()

# Modify loadAggregatedData to support passing date parameter

load_search = '''const daysFilter = document.getElementById('oi-days-filter');
        const days = daysFilter ? daysFilter.value : 30;

        if (!tbody || !chartArea) return;

        tbody.innerHTML = '<tr><td colspan="11" style="text-align:center; color:#888;">Fetching aggregated F&O data...</td></tr>';

        try {
            const res = await fetch(`/api/data/analysis/oi?days=${days}`);'''

load_replace = '''const daysFilter = document.getElementById('oi-days-filter');
        const days = daysFilter ? daysFilter.value : 30;
        const dateInput = document.getElementById('oi-quadrant-date');
        const targetDate = dateInput ? dateInput.value : '';

        if (!tbody || !chartArea) return;

        tbody.innerHTML = '<tr><td colspan="11" style="text-align:center; color:#888;">Fetching aggregated F&O data...</td></tr>';

        try {
            const res = await fetch(`/api/data/analysis/oi?days=${days}${targetDate ? '&target_date=' + targetDate : ''}`);'''

content = content.replace(load_search, load_replace)

with open(file_path, "w") as f:
    f.write(content)
