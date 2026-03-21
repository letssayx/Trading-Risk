import re

file_path = 'backend/ui/templates/workbench.html'
with open(file_path, 'r') as f:
    content = f.read()

# Make absolutely sure that `loadData` is called when Enter is pressed on Historical Data's #symbol-input

# Let's completely rewrite the 'Enter' key logic to be 100% robust by mapping inputIds directly to their load functions.
old_enter_logic = r"// Manual filters that trigger on input change for specific tabs.*?\/\/ 3\. Fallback: If still not found, check if there's a global fetcher bound to this specific input\n.*?\}"

# Create the explicit mapping fallback logic
new_enter_logic = """// Manual filters that trigger on input change for specific tabs
                    if (inputId === 'ca-search-input' && typeof filterCATable === 'function') filterCATable();
                    if (inputId === 'div-symbol-search' && typeof renderDividendsData === 'function') renderDividendsData();

                    // Explicit mapping for known input fields to their respective load functions
                    // This guarantees Enter will work, regardless of DOM structure
                    if (inputId === 'symbol-input' && typeof loadData === 'function') {
                        loadData();
                        return;
                    }
                    if (inputId === 'mr-symbol-input' && typeof applyMrFilter === 'function') {
                        applyMrFilter();
                        return;
                    }
                    if (inputId === 'market-activity-symbol' && typeof fetchMarketActivity === 'function') {
                        fetchMarketActivity();
                        return;
                    }
                    if (inputId === 'div-symbol-search' && typeof loadDividendsData === 'function') {
                        loadDividendsData();
                        return;
                    }
                    if (inputId === 'ca-search-input' && typeof loadCorporateActions === 'function') {
                        loadCorporateActions();
                        return;
                    }

                    // Auto trigger load button more robustly
                    // 1. Look for a button in the same container or parent container (up to 5 levels)
                    let currentEl = input;
                    let loadBtnFound = false;
                    for (let i = 0; i < 5; i++) {
                        if (!currentEl || currentEl.tagName === 'BODY') break;
                        const parent = currentEl.parentElement;
                        if (parent) {
                            const btns = Array.from(parent.querySelectorAll('button')).filter(btn =>
                                btn.innerText.toLowerCase().includes('load') ||
                                btn.innerText.toLowerCase().includes('refresh') ||
                                btn.innerText.toLowerCase().includes('get') ||
                                (btn.onclick && btn.onclick.toString().toLowerCase().includes('load'))
                            );
                            if (btns.length > 0) {
                                btns[0].click();
                                loadBtnFound = true;
                                break;
                            }
                        }
                        currentEl = parent;
                    }

                    // 2. If not found in immediate ancestry, look globally within the *closest active tab*
                    if (!loadBtnFound) {
                        const activeTab = input.closest('.main-tab-content') || document.querySelector('.main-tab-content.active');
                        if (activeTab) {
                            // Find the first Load/Refresh button inside this tab
                            const btns = Array.from(activeTab.querySelectorAll('button')).filter(btn =>
                                btn.innerText.toLowerCase().includes('load') ||
                                btn.innerText.toLowerCase().includes('refresh') ||
                                btn.innerText.toLowerCase().includes('get') ||
                                (btn.onclick && btn.onclick.toString().toLowerCase().includes('load'))
                            );
                            if (btns.length > 0) {
                                btns[0].click();
                                loadBtnFound = true;
                            }
                        }
                    }"""

content = re.sub(old_enter_logic, new_enter_logic, content, flags=re.DOTALL)

with open(file_path, 'w') as f:
    f.write(content)

print("Updated 'Enter' logic with explicit mappings.")
