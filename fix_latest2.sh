sed -i '/function toggleDateInputs(checkbox) {/i\
        function toggleDateInputsLatest(checkbox) {\
            const startInput = document.getElementById("start-date");\
            const endInput = document.getElementById("end-date");\
            const allDates = document.getElementById("all-dates-check");\
            if (checkbox.checked) {\
                startInput.value = "";\
                endInput.value = "";\
                startInput.disabled = true;\
                endInput.disabled = true;\
                if (allDates) {\
                    allDates.checked = false;\
                }\
            } else {\
                if (!allDates || !allDates.checked) {\
                    startInput.disabled = false;\
                    endInput.disabled = false;\
                    setDefaultDates();\
                }\
            }\
        }\
' backend/ui/templates/workbench.html
