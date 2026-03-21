sed -i '/<label for="all-dates-check" style="margin:0; font-size:12px;">All Dates<\/label>/a\
                    <input type="checkbox" id="latest-date-check" onchange="toggleDateInputsLatest(this)" checked>\
                    <label for="latest-date-check" style="margin:0; font-size:12px;">Latest</label>' backend/ui/templates/workbench.html
