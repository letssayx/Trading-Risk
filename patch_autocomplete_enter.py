import re

file_path = 'backend/ui/templates/workbench.html'
with open(file_path, 'r') as f:
    content = f.read()

# Let's replace the 'Enter' keydown logic in setupAutocomplete
old_enter_logic = """                } else if (e.key === 'Enter') {
                    e.preventDefault();
                    if (currentFocus > -1) {
                        if (items[currentFocus]) {
                            input.value = items[currentFocus].innerText;
                            dropdown.style.display = 'none';
                        }
                    }

                    dropdown.style.display = 'none';

                    // Auto trigger load button
                    const parentDiv = input.closest('div.flex') || input.closest('div.search-bar') || input.parentElement.parentElement;
                    if (parentDiv) {
                        const loadBtns = Array.from(parentDiv.querySelectorAll('button')).filter(btn => btn.innerText.toLowerCase().includes('load') || btn.innerText.toLowerCase().includes('refresh') || btn.innerText.toLowerCase().includes('get'));
                        if (loadBtns.length > 0) {
                            loadBtns[0].click();
                        } else {
                            // try finding any button in parent
                            const anyBtn = parentDiv.querySelector('button');
                            if (anyBtn) anyBtn.click();
                        }
                    }
                }"""

new_enter_logic = """                } else if (e.key === 'Enter') {
                    e.preventDefault();
                    if (currentFocus > -1) {
                        if (items[currentFocus]) {
                            input.value = items[currentFocus].innerText;
                            dropdown.style.display = 'none';
                        }
                    }

                    dropdown.style.display = 'none';

                    // Manual filters that trigger on input change for specific tabs
                    if (inputId === 'ca-search-input' && typeof filterCATable === 'function') filterCATable();
                    if (inputId === 'div-symbol-search' && typeof renderDividendsData === 'function') renderDividendsData();

                    // Auto trigger load button more robustly
                    // 1. Look for a button in the same container or parent container (up to 3 levels)
                    let currentEl = input;
                    let loadBtnFound = false;
                    for (let i = 0; i < 4; i++) {
                        if (!currentEl) break;
                        const parent = currentEl.parentElement;
                        if (parent) {
                            const btns = Array.from(parent.querySelectorAll('button')).filter(btn =>
                                btn.innerText.toLowerCase().includes('load') ||
                                btn.innerText.toLowerCase().includes('refresh') ||
                                btn.innerText.toLowerCase().includes('get') ||
                                btn.onclick && btn.onclick.toString().toLowerCase().includes('load')
                            );
                            if (btns.length > 0) {
                                btns[0].click();
                                loadBtnFound = true;
                                break;
                            }
                        }
                        currentEl = parent;
                    }

                    // 2. If not found, look globally within the current active tab
                    if (!loadBtnFound) {
                        const activeTab = document.querySelector('.main-tab-content.active');
                        if (activeTab) {
                            const btns = Array.from(activeTab.querySelectorAll('button')).filter(btn =>
                                btn.innerText.toLowerCase().includes('load') ||
                                btn.innerText.toLowerCase().includes('refresh') ||
                                btn.innerText.toLowerCase().includes('get') ||
                                btn.onclick && btn.onclick.toString().toLowerCase().includes('load')
                            );
                            if (btns.length > 0) {
                                btns[0].click();
                            }
                        }
                    }
                }"""

content = content.replace(old_enter_logic, new_enter_logic)

with open(file_path, 'w') as f:
    f.write(content)

print("Updated 'Enter' logic in autocomplete.")
