open(r'C:\ai-ca-copilot\ai-ca-copilot\frontend\.env', 'w').write('REACT_APP_API_URL=http://localhost:8000/api/v1\n')
print('Frontend .env fixed')

import urllib.request, json
data = json.dumps({'email':'demo@cacopilot.in','password':'demo@1234'}).encode()
req = urllib.request.Request('http://localhost:8000/api/v1/auth/login', data=data, headers={'Content-Type':'application/json'})
try:
    r = urllib.request.urlopen(req)
    print('LOGIN OK - backend works')
except Exception as e:
    print('LOGIN FAILED:', e)