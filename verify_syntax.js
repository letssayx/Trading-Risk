const fs = require('fs');
try {
  const code = fs.readFileSync('backend/ui/static/js/rolloverTool.js', 'utf8');
  eval(code);
  console.log("Syntax is valid.");
} catch (e) {
  if (e instanceof ReferenceError) {
    console.log("Syntax is valid (ReferenceError is normal outside browser).");
  } else {
    console.log("Error:", e);
  }
}
