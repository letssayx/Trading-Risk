sed -i "3285,3295c\\
                                loadBtnFound = true;\\
                            }\\
                        }\\
                    }\\
                }\\
            } else if (inputId === 'mr-symbol-input' && typeof applyMrFilter === 'function') {\\
                applyMrFilter();\\
            } else if (inputId === 'market-activity-symbol' && typeof fetchMarketActivity === 'function') {\\
                fetchMarketActivity();\\
            }\\
        });" backend/ui/templates/workbench.html
