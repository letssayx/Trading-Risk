import re

with open('backend/ui/templates/workbench.html', 'r') as f:
    content = f.read()

# Fix 1: Properly assign `window.divRawData = actions;` inside `loadDividendsData`
# Fix 2: Keep the search input intact during load so it can be used to filter the display
# We also update `downloadDividendsCSV` logic later. Let's do a targeted replace for `loadDividendsData`.

target_search = """        // Auto-clear symbol search on load per user request
        if (searchInput) searchInput.value = '';"""

replace_with = """        // Do NOT auto-clear symbol search so user can see what they filtered
        // if (searchInput) searchInput.value = '';"""

content = content.replace(target_search, replace_with)

target_search2 = """        if (meetingsArray.length > 0) {
             divMeetingsData = meetingsArray;
             divMeetingsData.sort((a, b) => new Date(b.meeting_date || b.date) - new Date(a.meeting_date || a.date));
        } else {
             divMeetingsData = [];
        }

        renderDividendsData();"""

replace_with2 = """        if (meetingsArray.length > 0) {
             divMeetingsData = meetingsArray;
             divMeetingsData.sort((a, b) => new Date(b.meeting_date || b.date) - new Date(a.meeting_date || a.date));
        } else {
             divMeetingsData = [];
        }

        // Store fetched dividend data globally
        window.divRawData = actions;

        renderDividendsData();"""

content = content.replace(target_search2, replace_with2)

with open('backend/ui/templates/workbench.html', 'w') as f:
    f.write(content)
