#!/bin/bash
git log -1 --stat
git show HEAD:frontend/static/js/opt_analysis.js > frontend/static/js/opt_analysis.js
ls -la frontend/static/js/opt_analysis.js
