sed -i 's/if (isLatest) url += "let url = `\/api\/data\/view\/list?type=${type}&limit=500`;latest=true";/if (isLatest) url += "\&latest=true";/' backend/ui/templates/workbench.html
