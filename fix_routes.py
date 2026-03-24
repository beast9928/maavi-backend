import re, os

app_js = r'C:\ai-ca-copilot\ai-ca-copilot\frontend\src\App.js'
content = open(app_js, encoding='utf-8').read()
print("Current routes in App.js:")
for line in content.split('\n'):
    if 'Route path' in line:
        print(' ', line.strip())