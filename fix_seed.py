content = open('app/models/invoice.py').read()
print('Enums found:')
import re
for m in re.findall(r'class (\w+)\(.*Enum', content):
    print(' ', m)