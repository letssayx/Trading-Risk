git restore backend/ui/templates/workbench.html
sed -i '3287,3293c\
                        }\
                    }\
                } else if (inputId === '\''mr-symbol-input'\'' && typeof applyMrFilter === '\''function'\'') {\
                    applyMrFilter();\
                } else if (inputId === '\''market-activity-symbol'\'' && typeof fetchMarketActivity === '\''function'\'') {\
                    fetchMarketActivity();\
                }\
            }\
        });' backend/ui/templates/workbench.html
