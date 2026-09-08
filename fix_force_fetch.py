import re

with open('backend/ui/templates/workbench.html', 'r') as f:
    content = f.read()

# Encode URI Component for force fetch job name to avoid spaces in URL
new_content = content.replace(
    'const res = await fetch(`/api/v1/cron/force-fetch/${encodeURIComponent(jobName)}`, { method: \'POST\' });',
    'const res = await fetch(`/api/v1/cron/force-fetch/${jobName}`, { method: \'POST\' });'
)

# And re-apply it properly using encodeURI component everywhere the actual call happens, or better, the JS function itself properly mapping jobName -> path
new_content = new_content.replace(
    'const res = await fetch(`/api/v1/cron/force-fetch/${jobName}`, { method: \'POST\' });',
    'const encodedJobName = encodeURIComponent(jobName);\n                const res = await fetch(`/api/v1/cron/force-fetch/${encodedJobName}`, { method: \'POST\' });'
)


with open('backend/ui/templates/workbench.html', 'w') as f:
    f.write(new_content)
