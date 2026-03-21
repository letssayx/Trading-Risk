sed -i 's/function toggleDateInputs(checkbox) {/function toggleDateInputs(checkbox) {\
            const latestDates = document.getElementById("latest-date-check");\
            if (checkbox.checked) {\
                if (latestDates) latestDates.checked = false;\
            }/' backend/ui/templates/workbench.html
