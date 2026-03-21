sed -i 's/} else if (inputId === '\''mr-symbol-input'\''/    } else if (inputId === '\''mr-symbol-input'\''/' backend/ui/templates/workbench.html
# Let's inspect line 1608 of script_14.js in the original template
grep -n "if (inputId === 'mr-symbol-input'" script_14.js
