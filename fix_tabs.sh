sed -i "3287,3289c\\
                        }\\
                    } else if (inputId === 'mr-symbol-input' && typeof applyMrFilter === 'function') {\\
                        applyMrFilter();" backend/ui/templates/workbench.html
