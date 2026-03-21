git restore backend/ui/templates/workbench.html
sed -i '3287,3302c\
                        }\
                    }\
                }\
            }\
        });\
\
        function addActive(items) {\
            if (!items) return false;\
            removeActive(items);\
            if (currentFocus >= items.length) currentFocus = 0;\
            if (currentFocus < 0) currentFocus = (items.length - 1);\
            items[currentFocus].classList.add("autocomplete-active");\
            items[currentFocus].scrollIntoView({ block: "nearest", behavior: "smooth" });\
        }' backend/ui/templates/workbench.html
