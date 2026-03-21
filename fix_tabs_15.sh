git restore backend/ui/templates/workbench.html
sed -i '3287,3293c\
                        }\
                    }\
                }\
            }\
        });\
\
        function addActive(items) {' backend/ui/templates/workbench.html
