import re

file_path = 'backend/ui/templates/workbench.html'
with open(file_path, 'r') as f:
    content = f.read()

# Replace setupAutocomplete function with the new version including keyboard nav and prompt
new_func = """        function setupAutocomplete(inputId) {
            const input = document.getElementById(inputId);
            if(!input) return;

            let dropdown = input.nextElementSibling;
            if (!dropdown || !dropdown.classList.contains('autocomplete-dropdown')) {
                dropdown = document.createElement('div');
                dropdown.className = 'autocomplete-dropdown';

                const wrapper = input.parentElement;
                if (!wrapper.classList.contains('autocomplete-wrapper')) {
                    const newWrapper = document.createElement('div');
                    newWrapper.className = 'autocomplete-wrapper';
                    input.parentNode.insertBefore(newWrapper, input);
                    newWrapper.appendChild(input);
                    newWrapper.appendChild(dropdown);
                } else {
                    wrapper.appendChild(dropdown);
                }
            }

            let currentFocus = -1;

            input.addEventListener('input', function() {
                const val = this.value.toUpperCase();
                dropdown.innerHTML = '';
                currentFocus = -1;

                if (!val) {
                    dropdown.style.display = 'none';
                    if (inputId === 'ca-search-input') {
                         if (typeof filterCATable === 'function') filterCATable();
                    } else if (inputId === 'div-symbol-search') {
                         if (typeof renderDividendsData === 'function') renderDividendsData();
                    }
                    return;
                }

                // If typing, trigger standard filters for some views
                if (inputId === 'ca-search-input') {
                     if (typeof filterCATable === 'function') filterCATable();
                } else if (inputId === 'div-symbol-search') {
                     if (typeof renderDividendsData === 'function') renderDividendsData();
                }

                const matches = [];
                for(let sym of allGlobalSymbols) {
                    if (sym.startsWith(val)) {
                        matches.push({sym: sym, dist: 0});
                    } else if (sym.includes(val)) {
                        matches.push({sym: sym, dist: 1});
                    } else if (val.length > 2) {
                        const lDist = levenshtein(val, sym);
                        if(lDist <= 2) {
                            matches.push({sym: sym, dist: lDist + 2});
                        }
                    }
                }

                matches.sort((a,b) => a.dist - b.dist);
                const topMatches = [...new Set(matches.map(m => m.sym))].slice(0, 10);

                if (topMatches.length > 0) {
                    topMatches.forEach(sym => {
                        const div = document.createElement('div');
                        div.innerText = sym;

                        // Highlight matching part
                        const matchIndex = sym.indexOf(val);
                        if (matchIndex !== -1) {
                            div.innerHTML = sym.substring(0, matchIndex) +
                                            "<strong>" + sym.substring(matchIndex, matchIndex + val.length) + "</strong>" +
                                            sym.substring(matchIndex + val.length);
                        }

                        div.addEventListener('mousedown', function(e) {
                            e.preventDefault();
                            input.value = sym;
                            dropdown.style.display = 'none';

                            // Auto trigger load button if it exists next to it
                            const loadBtn = input.parentElement.parentElement.querySelector('button');
                            if (loadBtn && (loadBtn.innerText.toLowerCase().includes('load') || loadBtn.innerText.toLowerCase().includes('refresh'))) {
                                loadBtn.click();
                            }

                            if (inputId === 'ca-search-input' && typeof filterCATable === 'function') filterCATable();
                            if (inputId === 'div-symbol-search' && typeof renderDividendsData === 'function') renderDividendsData();
                        });
                        dropdown.appendChild(div);
                    });
                    dropdown.style.display = 'block';
                } else {
                    dropdown.style.display = 'none';
                }
            });

            input.addEventListener('keydown', function(e) {
                const items = dropdown.getElementsByTagName('div');
                if (e.key === 'ArrowDown') {
                    currentFocus++;
                    addActive(items);
                    e.preventDefault();
                } else if (e.key === 'ArrowUp') {
                    currentFocus--;
                    addActive(items);
                    e.preventDefault();
                } else if (e.key === 'Enter') {
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
                }
            });

            function addActive(items) {
                if (!items) return false;
                removeActive(items);
                if (currentFocus >= items.length) currentFocus = 0;
                if (currentFocus < 0) currentFocus = (items.length - 1);
                items[currentFocus].classList.add('autocomplete-active');
                // Scroll into view if needed
                items[currentFocus].scrollIntoView({ block: 'nearest', behavior: 'smooth' });
            }

            function removeActive(items) {
                for (let i = 0; i < items.length; i++) {
                    items[i].classList.remove('autocomplete-active');
                }
            }

            input.addEventListener('blur', () => {
                setTimeout(() => { dropdown.style.display = 'none'; }, 200);
            });
            input.addEventListener('focus', () => {
                if(input.value && dropdown.children.length > 0) {
                    dropdown.style.display = 'block';
                }
            });
        }"""

pattern = r'        function setupAutocomplete\(inputId\) \{.*?\n        \}\n'
new_content = re.sub(pattern, new_func + '\n', content, flags=re.DOTALL)

with open(file_path, 'w') as f:
    f.write(new_content)
