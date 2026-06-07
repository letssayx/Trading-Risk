import re
import os

filepath = 'backend/ui/static/js/fiiTool.js'
with open(filepath, 'r') as f:
    content = f.read()

search = """window.loadFiiTrendChart = async function(overrideDays) {
    console.log("Loading FII Trend Chart...");
    try {
        const days = overrideDays || document.getElementById("fii-analysis-days")?.value || "30";"""

replace = """window.loadFiiTrendChart = async function(overrideDays) {
    console.log("Loading FII Trend Chart...");
    try {
        const days = (overrideDays && typeof overrideDays !== 'object') ? overrideDays : (document.getElementById("fii-analysis-days")?.value || "30");"""

if search in content:
    content = content.replace(search, replace)
    with open(filepath, 'w') as f:
        f.write(content)
    print("fiiTool.js patched")
else:
    print("Could not find block in fiiTool.js")
