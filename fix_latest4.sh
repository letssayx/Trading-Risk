sed -i 's/let url = `\/api\/data\/view\/list?type=${type}&limit=500`;/const latestCheck = document.getElementById("latest-date-check");\
                const isLatest = latestCheck \&\& latestCheck.checked;\
                let limit = type === "mwpl" ? 5000 : 500;\
                let url = `\/api\/data\/view\/list?type=${type}\&limit=${limit}`;\
                if (isLatest) url += "&latest=true";/' backend/ui/templates/workbench.html
